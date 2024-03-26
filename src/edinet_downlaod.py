import os
from datetime import date, timedelta
from logging import getLogger
from typing import Optional

import requests

from common.configs import configs
from common.logger import init_logger

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
            1: メタ情報のみ, 2: メタ情報と文書データ. defaults to None (メタ情報のみ).

    Returns:
        Optional[requests.Response]: 成功時はレスポンスオブジェクト、失敗時はNone
    """
    logger.info("Fetching EDINET document data for day: %s", day)

    if doc_type is None:
        doc_type = configs.EdinetApi.DOC_TYPE_ONLY_META

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
        params = {"type": configs.EdinetApi.DOC_TYPE_ONLY_META}
        res = requests.get(
            url, params=params, stream=True, timeout=configs.EdinetApi.TIME_OUT
        )
        res.raise_for_status()  # 200以外のステータスコードをエラーとして扱う
        return res
    except requests.RequestException as e:
        logger.error(f"書類の取得に失敗しました。doc_id={doc_id}, エラー: {e}")
        return None
