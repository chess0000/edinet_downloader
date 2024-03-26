from datetime import date, timedelta
from typing import Optional

import pytest
import requests
import requests_mock

from common.configs import configs
from edinet_downlaod import fetch_edinet_document_json, generate_date_sequence


@pytest.mark.parametrize(
    ["start_date", "end_date", "expected"],
    [
        pytest.param(
            date(2021, 1, 1),
            date(2021, 1, 3),
            [date(2021, 1, 1), date(2021, 1, 2), date(2021, 1, 3)],
            id="normal",
        ),
        pytest.param(
            date(2021, 1, 1),
            date(2021, 1, 1),
            [date(2021, 1, 1)],
            id="same_date",
        ),
        pytest.param(
            date(2021, 1, 2),
            date(2021, 1, 1),
            ValueError,
            id="end_date_is_before_start_date",
        ),
        pytest.param(
            date.today(),
            date.today(),
            [date.today()],
            id="today",
        ),
        pytest.param(
            date.today() - timedelta(days=3),
            None,
            [
                date.today() - timedelta(days=3),
                date.today() - timedelta(days=2),
                date.today() - timedelta(days=1),
                date.today(),
            ],
            id="end_date_is_none",
        ),
    ],
)
def test_generate_date_sequence(
    start_date: date, end_date: Optional[date], expected: list[date] | Exception
) -> None:
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            generate_date_sequence(start_date, end_date)
    else:
        assert generate_date_sequence(start_date, end_date) == expected


@pytest.mark.parametrize(
    ["day", "doc_type", "expected"],
    [
        pytest.param(
            date(2024, 3, 25),
            configs.EdinetApi.DOC_TYPE_ONLY_META,
            200,
            id="doc_type_1",
        ),
        pytest.param(
            date(2024, 3, 25),
            configs.EdinetApi.DOC_TYPE_META_AND_DOC_DATA,
            200,
            id="doc_type_2",
        ),
    ],
)
def test_fetch_edinet_document_data(
    day: date, doc_type: str, expected: requests.Response
) -> None:
    with requests_mock.Mocker() as m:
        m.get(
            "mock://testurl", status_code=expected
        )  # モックURLと期待されるステータスコードを設定
        # API URLをモックURLに一時的に置き換え
        configs.EdinetApi.DOC_JSON_URL = "mock://testurl"

        response = fetch_edinet_document_json(day, doc_type)
        assert response.status_code == expected
