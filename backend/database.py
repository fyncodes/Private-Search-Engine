import sqlite3
import hashlib
from pathlib import Path


# Find the main project folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Data folder
DATA_DIR = BASE_DIR / "data"

# Create data folder if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)

# Database file
DB_PATH = DATA_DIR / "search.db"


def get_connection():
    """
    Create a connection to the SQLite database.
    """

    connection = sqlite3.connect(DB_PATH)

    # Allows us to access database columns by name
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """
    Create the documents table if it doesn't exist.
    """

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            content TEXT,
            word_count INTEGER DEFAULT 0,
            content_hash TEXT,
            document_type TEXT DEFAULT 'html',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
    """)

    connection.commit()

    connection.close()

    migrate_database()

def save_document(url, title, content, document_type="html"):
    connection = get_connection()

    word_count = len(content.split())

    content_hash = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    existing = connection.execute("""
        SELECT content_hash
        FROM documents
        WHERE url = ?
    """, (url,)).fetchone()

    if existing is None:
        connection.execute("""
            INSERT INTO documents (
                url,
                title,
                content,
                word_count,
                content_hash,
                document_type,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            url,
            title,
            content,
            word_count,
            content_hash,
            document_type
        ))

        connection.commit()
        connection.close()

        return "new"

    if existing["content_hash"] == content_hash:
        connection.execute("""
            UPDATE documents
            SET document_type = ?
            WHERE url = ?
        """, (
            document_type,
            url
        ))

        connection.commit()
        connection.close()

        return "unchanged"

    connection.execute("""
        UPDATE documents
        SET title = ?,
            content = ?,
            word_count = ?,
            content_hash = ?,
            document_type = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE url = ?
    """, (
        title,
        content,
        word_count,
        content_hash,
        document_type,
        url
    ))

    connection.commit()
    connection.close()

    return "updated"

def get_documents():
    """
    Get all documents from the database.
    """

    connection = get_connection()

    documents = connection.execute("""
        SELECT id, url, title, content, document_type
        FROM documents
    """).fetchall()

    connection.close()

    return documents

def migrate_database():
    connection = get_connection()

    columns = connection.execute(
        "PRAGMA table_info(documents)"
    ).fetchall()

    existing_columns = {
        column["name"]
        for column in columns
    }

    if "word_count" not in existing_columns:
        connection.execute(
            "ALTER TABLE documents "
            "ADD COLUMN word_count INTEGER DEFAULT 0"
        )

    if "content_hash" not in existing_columns:
        connection.execute(
            "ALTER TABLE documents "
            "ADD COLUMN content_hash TEXT"
        )

    if "updated_at" not in existing_columns:
        connection.execute(
            "ALTER TABLE documents "
            "ADD COLUMN updated_at TIMESTAMP"
        )

        connection.execute(
            "UPDATE documents "
            "SET updated_at = CURRENT_TIMESTAMP "
            "WHERE updated_at IS NULL"
        )

    if "document_type" not in existing_columns:
        connection.execute(
            "ALTER TABLE documents "
            "ADD COLUMN document_type TEXT DEFAULT 'html'"
        )

    connection.commit()
    connection.close()

    print("Database migration completed.")

def populate_metadata():
    connection = get_connection()

    documents = connection.execute("""
        SELECT id, content
        FROM documents
    """).fetchall()

    for document in documents:
        content = str(document["content"] or "")

        word_count = len(content.split())

        content_hash = hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

        connection.execute("""
            UPDATE documents
            SET word_count = ?,
                content_hash = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            word_count,
            content_hash,
            document["id"]
        ))

    connection.commit()
    connection.close()

    print(
        f"Metadata populated for "
        f"{len(documents)} documents."
    )