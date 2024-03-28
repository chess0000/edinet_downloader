import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configs(BaseSettings):
    """全体で使用するConfig情報を一元管理するためのClass
    環境毎に異なる設定は.envに記述して読み込む
    全環境で共通の設定は、以下に直接記述する
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # .envファイルから読み込む
    ENV: str
    BASE_PATH_DOWNLOAD_ZIP: str
    BASE_PATH_CHECK_DOWNLOADED_DB: str

    # 直接記述
    PROJECT_ROOT_PATH: str = os.path.join(
        Path(__file__).parent.parent.parent.absolute()
    )

    SRC_DIR_PATH: str = os.path.join(PROJECT_ROOT_PATH, "src")
    LOGGER_CONFIG_PATH: str = os.path.join(SRC_DIR_PATH, "logger_config.yaml")

    LOG_DIR_PATH: str = os.path.join(PROJECT_ROOT_PATH, "logs")

    FILE_NAME_EDINET_SUBMISSIONS_DB: str = "edinet_submissions.db"

    class EdinetApi:
        BASE_URL: str = "https://disclosure.edinet-fsa.go.jp/api/v1"
        DOC_URL: str = os.path.join(BASE_URL, "documents")
        DOC_JSON_URL = os.path.join(BASE_URL, "documents.json")

        DOC_TYPE_ONLY_META: str = "1"  # メタ情報のみ
        DOC_TYPE_META_AND_DOC_DATA: str = "2"  # メタ情報と文書データ

        ## 有価証券報告書の書式 ##
        # 1: 提出本文書及び監査報告書XBRLファイル
        # 2: PDF
        # 3: 代替書面・添付文書
        # 4: 英文ファイル
        DOC_TYPE_XBRL: str = "1"
        DOC_TYPE_PDF: str = "2"

        TIME_OUT: int = 30

    class EdinetDocument:
        SECURITIES_REPORT_CODE = "030000"
        AMENDED_SECURITIES_REPORT_CODE = "030001"
        QUARTERLY_REPORT_CODE = "043000"
        AMENDED_QUARTERLY_REPORT_CODE = "043001"

        CORPORATE_CONTENT_CODE = "010"


configs = Configs()
