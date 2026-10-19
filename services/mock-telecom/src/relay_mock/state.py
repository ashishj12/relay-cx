
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path


class SyntheticState:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS identities (digest TEXT PRIMARY KEY, customer TEXT, expires REAL);
                CREATE TABLE IF NOT EXISTS receipts (
                    customer TEXT, operation TEXT, body TEXT, PRIMARY KEY(customer, operation)
                );
            """)

    def issue(self, token, customer, expires):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute(
                "INSERT OR REPLACE INTO identities VALUES (?,?,?)",
                (hashlib.sha256(token.encode()).hexdigest(), customer, expires),
            )

    def identity(self, token):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute(
                "SELECT customer,expires FROM identities WHERE digest=?",
                (hashlib.sha256(token.encode()).hexdigest(),),
            ).fetchone()

    def receipt(self, customer, operation):
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute(
                "SELECT body FROM receipts WHERE customer=? AND operation=?", (customer, operation)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def create(self, record):
        with closing(sqlite3.connect(self.path)) as db, db:
            changed = db.execute(
                "INSERT OR IGNORE INTO receipts VALUES (?,?,?)",
                (record["customerId"], record["idempotencyKey"], json.dumps(record)),
            ).rowcount
        return bool(changed)
