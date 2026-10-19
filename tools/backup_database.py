"""Create an online-consistent SQLite snapshot without overwriting an existing backup."""

import argparse
import os
from pathlib import Path
import sqlite3

def backup(database: Path, output: Path) -> None:
    source = database.resolve(strict=True)
    output = output.resolve()
    if source == output:
        raise ValueError("backup_must_be_separate")
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    try:
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as origin:
            with sqlite3.connect(output) as destination:
                origin.backup(destination)
                if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("backup_integrity_failed")
    except Exception:
        output.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    backup(args.database, args.output)
    print("Consistent database backup verified; protect it as sensitive runtime data.")
