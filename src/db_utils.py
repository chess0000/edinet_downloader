import sqlite3
from datetime import date


def insert_company(db_path: str, filer_name: str, sec_code: str) -> int:
    """会社情報をinsertし、company_idを返す"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO companies (filer_name, sec_code) VALUES (?, ?)",
        (filer_name, sec_code),
    )
    conn.commit()

    cursor.execute(
        "SELECT company_id FROM companies WHERE filer_name = ? AND sec_code = ?",
        (filer_name, sec_code),
    )
    company_id = cursor.fetchone()[0]

    conn.close()
    return company_id


def insert_document(
    db_path: str,
    doc_id: str,
    submission_date: date,
    company_id: int,
    downloaded: bool = False,
) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO documents
            (doc_id, submission_date, company_id, downloaded)
        VALUES
            (?, ?, ?, ?)
        """,
        (doc_id, submission_date, company_id, downloaded),
    )

    conn.commit()
    conn.close()
