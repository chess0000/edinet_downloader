import os
import sqlite3

from common.configs import configs


def make_file_dot_gitignore(base_path: str) -> None:
    """指定したbaseディレクトリに.gitignoreを追加して、base以下のファイルを全て無視する。

    Args:
        base_path (str): .gitignoreを追加するファイルのパス

    Returns:
        None
    """
    if not os.path.exists(base_path):
        assert f"{base_path} does not exist."

    dot_gitignore_file_path = os.path.join(base_path, ".gitignore")

    with open(dot_gitignore_file_path, "w") as f:
        f.write("*\n")


def initialize_db(db_base_path: str = configs.BASE_PATH_CHECK_DOWNLOADED_DB) -> None:
    """EDINET提出書類の一覧を管理するためのdbの初期化

    Args:
        db_base_path (str): dbのパス。環境変数からデフォルト値を取得する。

    Returns:
        None
    """
    if not os.path.exists(db_base_path):
        os.makedirs(db_base_path)

    db_file_path = os.path.join(db_base_path, configs.FILE_NAME_EDINET_SUBMISSIONS_DB)

    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()

    # companiesテーブルの作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            company_id INTEGER PRIMARY KEY AUTOINCREMENT,
            filer_name TEXT NOT NULL,
            sec_code TEXT NOT NULL,
            UNIQUE(filer_name, sec_code)
        );
    """)

    # documentsテーブルの作成（filer_nameとsec_codeを削除し、company_idを追加）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            submission_date DATE NOT NULL,
            company_id INTEGER NOT NULL,
            downloaded INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (company_id) REFERENCES companies(company_id)
        );
    """)

    # 各列にインデックスを作成
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_submission_date ON documents (submission_date);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_company_id ON documents (company_id);"
    )

    conn.commit()
    conn.close()

    make_file_dot_gitignore(db_base_path)


def initialize_downloaded_dir(
    downloaded_base_path: str = configs.BASE_PATH_DOWNLOAD_ZIP,
) -> None:
    """ダウンロードした有価証券報告書を保存するためのディレクトリを作成する

    Args:
        downloaded_base_path (str):
            ダウンロードした有価証券報告書を保存するディレクトリのパス。
            デフォルト値はconfigs.pyから取得する。

    Returns:
        None
    """
    if not os.path.exists(downloaded_base_path):
        os.makedirs(downloaded_base_path)

    make_file_dot_gitignore(downloaded_base_path)


def initialize_log(log_base_path: str = configs.LOG_DIR_PATH) -> None:
    """ログファイルを保存するためのディレクトリを作成する

    Args:
        log_base_path (str): ログファイルのパス。デフォルト値はconfigs.pyから取得する。

    Returns:
        None
    """
    if not os.path.exists(log_base_path):
        os.makedirs(log_base_path)

    make_file_dot_gitignore(log_base_path)


def main() -> None:
    initialize_db()
    initialize_downloaded_dir()
    initialize_log()


if __name__ == "__main__":
    main()
