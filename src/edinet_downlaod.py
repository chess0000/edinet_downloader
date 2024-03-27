import os
from datetime import date, timedelta
from logging import getLogger
from typing import Optional

import requests

from common.configs import configs
from common.logger import init_logger
from db_init import find_documents_by_date, insert_document

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


def fetch_edinet_document_json(
    day: date, doc_type: Optional[str] = None
) -> Optional[requests.Response]:
    """EDINET APIから指定日のドキュメントデータを取得する

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


def extract_first_securities_report_id(res: requests.Response) -> str:
    """EDINETから取得したJSONデータから最初に条件に一致するdocIDを抽出する

    Args:
        res (requests.Response): レスポンス

    Returns:
        str: 条件に一致する最初のdocID。なければ空文字を返す。
    """
    json_data = res.json()
    for result in json_data["results"]:
        is_securities_report = (
            result["ordinanceCode"] == configs.EdinetDocument.CORPORATE_CONTENT_CODE
            and result["formCode"] == configs.EdinetDocument.SECURITIES_REPORT_CODE
        )

        if is_securities_report:
            logger.info(
                "filerName: %s, Description: %s, docID: %s",
                result["filerName"],
                result["docDescription"],
                result["docID"],
            )
            return result["docID"]

    return ""


def get_edinet_document_id(day: date) -> str:
    """指定された日付における最初の有価証券報告書のドキュメントIDを取得する。

    Args:
        day (date): ドキュメントを取得する日付。

    Returns:
        str: 条件に一致する最初のドキュメントID。なければ空文字を返す。
    """
    res = fetch_edinet_document_json(day)
    if res is None:
        logger.error("Response from EDINET API is None.")
        return ""
    if not res.ok:
        logger.error(
            f"Response from EDINET API is not OK. Status code: {res.status_code}"
        )
        return ""

    return extract_first_securities_report_id(res)


def fetch_securities_report(doc_id: str) -> Optional[requests.Response]:
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
    doc_id: str,
    day: date,
    db_path: str = configs.DB_PATH_CHECK_DOWNLOADED,
    root_path: Optional[str] = None,
) -> None:
    """有価証券報告書のzipファイルをダウンロードする

    Args:
        doc_id (str): 書類のID
        day (date): 書類の提出日
        db_path (str): ダウンロード済みの書類を記録するデータベースのパス
        root_path (Optional[str], optional): zipファイルを保存するディレクトリのパス
    """
    if root_path is None:
        root_path = configs.DOWNLOAD_ZIP_ROOT_PATH

    documents = find_documents_by_date(db_path, day)

    already_downloaded = any(doc[0] == doc_id and doc[1] for doc in documents)
    if already_downloaded:
        logger.debug(f"{doc_id=} is already downloaded. Skipping download.")
        return

    # 年/月/日のディレクトリパスを作成。(YYYY/MM/DD)。
    year_dir = day.strftime("%Y")
    month_dir = day.strftime("%m")
    day_dir = day.strftime("%d")
    target_path = os.path.join(root_path, year_dir, month_dir, day_dir)

    if not os.path.exists(target_path):
        logger.debug(f"Directory does not exist. Creating a new one. {target_path=}")
        os.makedirs(target_path)

    zip_file_path = os.path.join(target_path, f"{doc_id}.zip")
    # 既にファイルが存在する場合はダウンロードをスキップ
    if os.path.exists(zip_file_path):
        logger.debug(f"Zip file {zip_file_path} already exists. Skipping download.")
        return

    # 指定のdoc_idの有価証券報告書をダウンロード
    res = fetch_securities_report(doc_id)
    if res is None:
        logger.error(f"Failed to fetch securities report. {doc_id=}")
        return

    with open(zip_file_path, "wb") as f:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    # ダウンロード済みの書類をデータベースに記録
    insert_document(db_path, doc_id, day, True)
    logger.info(f"Downloaded zip file: {zip_file_path}")
