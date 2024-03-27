import sqlite3
from datetime import date

from common.configs import configs


# データベースへの接続を確立し、テーブルとインデックスを作成する
def initialize_db(db_path: str) -> None:
    # データベースへの新しい接続を確立
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 新しいテーブルを作成（filer_nameとsec_codeカラムを追加）
    cursor.execute("""
        CREATE TABLE documents (
            doc_id TEXT PRIMARY KEY,
            submission_date DATE NOT NULL,
            filer_name TEXT,
            sec_code TEXT,
            downloaded BOOLEAN NOT NULL DEFAULT FALSE
        );
    """)

    # submission_date列にインデックスを作成
    cursor.execute("""
        CREATE INDEX idx_submission_date ON documents (submission_date);
    """)

    conn.commit()
    conn.close()


def insert_document(
    db_path: str,
    doc_id: str,
    submission_date: date,
    filer_name: str,
    sec_code: str,
    downloaded: bool = False,
) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO documents
            (doc_id, submission_date, filer_name, sec_code, downloaded)
        VALUES
            (?, ?, ?, ?, ?)
        """,
        (doc_id, submission_date, filer_name, sec_code, downloaded),
    )

    conn.commit()
    conn.close()


# 特定の日付に提出された書類を検索する
def find_documents_by_date(
    db_path: str, submission_date: date
) -> list[tuple[str, bool]]:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT doc_id, downloaded FROM documents WHERE submission_date = ?",
        (submission_date,),
    )

    documents = cursor.fetchall()
    conn.close()

    return documents


if __name__ == "__main__":
    db_path = configs.DB_PATH_CHECK_DOWNLOADED
    initialize_db(db_path)
