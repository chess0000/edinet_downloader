import os
import sqlite3
from datetime import date, timedelta
from logging import getLogger
from typing import Generator, Optional

import requests

from common.configs import configs
from common.logger import init_logger
from db_utils import insert_company, insert_document

init_logger(configs.LOGGER_CONFIG_PATH)

logger = getLogger(__name__)


def generate_date_sequence(
    start_date: date = date.today(),
    end_date: Optional[date] = None,
) -> list[date]:
    """2つの日付の間の日付のリストを生成する

    Args:
        start_date (datetime.date): 開始日。デフォルトは今日
        end_date (datetime.date): 終了日。
            Noneの場合は開始日と同じと見なされる。デフォルトはNone。

    Returns:
        list[datetime.date]: 2つの日付の間の日付のリスト
    """
    if end_date is None:
        end_date = date.today()

    if end_date < start_date:
        raise ValueError("end_date must not be before start_date")

    logger.info("start_date: %s", start_date)
    logger.info("end_day: %s", end_date)

    days_range = (end_date - start_date).days

    date_list = [start_date + timedelta(days=i) for i in range(int(days_range))]
    date_list.append(end_date)

    return date_list


def fetch_edinet_submission_documents(
    day: date, doc_type: Optional[str] = None
) -> Optional[requests.Response]:
    """EDINET APIから指定日に提出されたドキュメント一覧をjson形式で取得する

    Args:
        day (date): 取得する日付
        doc_type (Optional[str], optional): 取得するドキュメントの種類.
            1: メタ情報のみ, 2: メタ情報と文書データ. defaults to None (2).

    Returns:
        Optional[requests.Response]: 成功時はレスポンスオブジェクト、失敗時はNone
    """
    logger.info("Fetching EDINET document data for day: %s", day)

    if doc_type is None:
        doc_type = configs.EdinetApi.DOC_TYPE_META_AND_DOC_DATA

    url = configs.EdinetApi.DOC_JSON_URL
    params = {"date": day.strftime("%Y-%m-%d"), "type": doc_type}

    try:
        res = requests.get(url, params=params, timeout=configs.EdinetApi.TIME_OUT)
        res.raise_for_status()  # 200以外のステータスコードをエラーとして扱う
        return res
    except requests.RequestException as e:
        logger.error(f"Failed to fetch EDINET document data: {e}")
        return None


def extract_securities_info(
    res: requests.Response,
) -> Generator[tuple[str, str, str], None, None]:
    """EDINETから取得したJSONデータから最初に条件に一致する
       filerName, docID, secCodeを抽出する

    Args:
        res (requests.Response): レスポンス

    Returns:
        Generator[Tuple[str, str, str], None, None]:
            タプル(filerName: 銘柄名, docID: 書類管理番号, secCode: 証券コード)
    """
    json_data = res.json().get("results", [])  # resultsキーが存在しない->空リストを返す
    for result in json_data:
        is_securities_report = (
            result.get("ordinanceCode") == configs.EdinetDocument.CORPORATE_CONTENT_CODE
            and result.get("formCode") == configs.EdinetDocument.SECURITIES_REPORT_CODE
        )

        # secCodeが存在するかどうかで上場企業かどうかを判定
        is_listed_company = result.get("secCode") is not None

        if is_securities_report and is_listed_company:
            yield (result.get("filerName"), result.get("docID"), result.get("secCode"))


def fetch_edinet_document_binary(doc_id: str) -> Optional[requests.Response]:
    """docIDから書類を取得する

    Args:
        doc_id (str): 書類のID

    Returns:
        Optional[requests.Response]:
            成功時はレスポンスオブジェクト。有価証券報告書のzipファイルが格納されている。
            失敗時はNone
    """
    try:
        url = os.path.join(configs.EdinetApi.DOC_URL, doc_id)
        params = {"type": configs.EdinetApi.DOC_TYPE_XBRL}
        res = requests.get(
            url, params=params, stream=True, timeout=configs.EdinetApi.TIME_OUT
        )
        res.raise_for_status()  # 200以外のステータスコードをエラーとして扱う
        return res
    except requests.RequestException as e:
        logger.error(f"書類の取得に失敗しました。doc_id={doc_id}, エラー: {e}")
        return None


def download_securities_report_zip(
    day: date,
    filer_name: str,
    doc_id: str,
    sec_code: str,
    binary_res: requests.Response,
    db_path: str = configs.BASE_PATH_CHECK_DOWNLOADED_DB,
    root_path: Optional[str] = None,
) -> None:
    """有価証券報告書のzipファイルをダウンロードする"""
    if root_path is None:
        root_path = configs.BASE_PATH_DOWNLOAD_ZIP

    # 会社情報をデータベースに登録し、company_idを取得
    company_id = insert_company(db_path, filer_name, sec_code)

    # データベースに記録されているか確認
    already_downloaded = check_document_downloaded(db_path, doc_id)
    if already_downloaded:
        logger.debug(f"{doc_id=} is already downloaded. Skipping download.")
        return

    # 年/月/日のディレクトリパスを作成
    year_dir, month_dir, day_dir = (
        day.strftime("%Y"),
        day.strftime("%m"),
        day.strftime("%d"),
    )
    target_path = os.path.join(root_path, year_dir, month_dir, day_dir)
    os.makedirs(target_path, exist_ok=True)

    zip_file_path = os.path.join(target_path, f"{doc_id}.zip")
    if os.path.exists(zip_file_path):
        logger.debug(f"Zip file {zip_file_path} already exists. Skipping download.")
        return

    # ダウンロード処理
    with open(zip_file_path, "wb") as f:
        for chunk in binary_res.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
        logger.info(f"Downloaded zip file: {zip_file_path}")

    # ダウンロード済みの書類をデータベースに記録
    insert_document(db_path, doc_id, day, company_id, True)


def check_document_downloaded(db_path: str, doc_id: str) -> bool:
    """文書がダウンロード済みかどうかをデータベースから確認する"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT downloaded FROM documents WHERE doc_id = ?", (doc_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0]
