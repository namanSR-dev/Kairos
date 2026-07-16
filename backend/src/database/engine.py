import os
import sys
from sqlmodel import create_engine, SQLModel
from pathlib import Path

# Determine AppData storage path for Windows
if sys.platform == "win32":
    appdata = os.environ.get("APPDATA")
    storage_dir = Path(appdata) / "Kairos" if appdata else Path.home() / "AppData" / "Roaming" / "Kairos"
else:
    # Fallback for local testing on Mac/Linux if needed
    storage_dir = Path.home() / ".kairos"

# Ensure the directory exists
storage_dir.mkdir(parents=True, exist_ok=True)
sqlite_file_name = storage_dir / "storage.db"

# Format the URL correctly for SQLAlchemy (SQLite requires sqlite:///)
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
