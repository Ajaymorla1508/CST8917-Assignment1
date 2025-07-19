import logging
import pyodbc
import os

def main(metadata: dict) -> None:
    conn_str = os.environ["SqlConnectionString"]
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ImageMetadata (FileName, FileSizeKB, Width, Height, Format)
            VALUES (?, ?, ?, ?, ?)""",
            metadata["file_name"], metadata["size_kb"],
            metadata["width"], metadata["height"],
            metadata["format"]
        )
        conn.commit()
    logging.info("Metadata stored successfully.")
