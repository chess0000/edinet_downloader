from pathlib import Path

from src.setup_enviroment import (
    initialize_db,
    initialize_downloaded_dir,
    initialize_log,
)

from common.configs import configs


def test_initialize_db(tmp_path: Path) -> None:
    """ファイル生成ができるか確認する

    Args:
        tmp_path (Path): pytestのfixture。一時ディレクトリのPathオブジェクト
    """
    db_path = tmp_path / "db"
    db_file_path = db_path / configs.FILE_NAME_EDINET_SUBMISSIONS_DB
    initialize_db(str(db_path))  # テスト対象の引数がstr型なので、str型に変換して渡す
    assert db_file_path.exists()


def test_initialize_downloaded_dir(tmp_path: Path) -> None:
    download_path = tmp_path / "downloads"
    gitignore_path = download_path / ".gitignore"
    initialize_downloaded_dir(str(download_path))
    assert download_path.exists()  # テスト対象の引数がstr型なので、str型に変換して渡す
    assert gitignore_path.is_file()


def test_initialize_log(tmp_path: Path) -> None:
    log_path = tmp_path / "logs"
    gitignore_path = log_path / ".gitignore"
    initialize_log(str(log_path))  # テスト対象の引数がstr型なので、str型に変換して渡す
    assert log_path.exists()
    assert gitignore_path.is_file()
