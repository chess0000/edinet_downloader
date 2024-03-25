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


def fetch_edinet_docmment_data(
    day: date, doc_type: Optional[str] = configs.EdinetApi.DOC_TYPE_ONLY_META
) -> requests.Response:
    """EDINET APIから指定日のドキュメントデータを取得する

    Args:
        day (date): 取得する日付
        doc_type (str, optional): 取得するドキュメントの種類.
            1: メタ情報のみ, 2: メタ情報と文書データ. defaults: 1

    Returns:
        requests.Response: ドキュメントデータ
    """
    logger.info("fetch_edinet_docmment_data")
    logger.info("day: %s", day)

    url = configs.EdinetApi.DOC_JSON_URL
    params = {"date": day, "type": doc_type}

    return requests.get(url, params=params, timeout=configs.EdinetApi.TIME_OUT)
