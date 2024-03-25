import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configs(BaseSettings):
    """全体で使用するConfig情報を一元管理するためのClass
    環境毎に異なる設定は.envに記述して読み込む
    全環境で共通の設定は、以下に直接記述する
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ENV: str
    VERSION: str = "0.0.1"

    SRC_DIR_PATH: str = os.path.join(Path(__file__).parent.parent.absolute())
    LOGGER_CONFIG_PATH: str = os.path.join(SRC_DIR_PATH, "logger_config.yaml")

    class EdinetApi:
        BASE_URL: str = "https://disclosure.edinet-fsa.go.jp/api/v1"
        DOC_URL: str = os.path.join(BASE_URL, "documents")
        DOC_JSON_URL = os.path.join(BASE_URL, "documents.json")

        DOC_TYPE_ONLY_META: str = "1"  # メタ情報のみ
        DOC_TYPE_META_AND_DOC_DATA: str = "2"  # メタ情報と文書データ

        TIME_OUT: int = 30


configs = Configs()
