from pathlib import Path

from db.db_main import create_db

PROJECT_ROOT: Path = Path(__file__).resolve().parent
DB_PATH: Path = PROJECT_ROOT / "db" / "database.db"


def main() -> None:
    create_db()


if __name__ == "__main__":
    main()
