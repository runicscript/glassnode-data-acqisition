import sqlite3
from datetime import date, datetime
from pathlib import Path

from config import DATABASE_URL, DB_BACKEND, SQLITE_PATH

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - optional dependency until postgres is used
    psycopg = None
    dict_row = None


class DBHandler:
    def __init__(self, configs=None):
        self.configs = configs
        self.backend = DB_BACKEND
        self.database_url = DATABASE_URL
        self.db_path = Path(SQLITE_PATH)
        self.conn = None

    def connect(self):
        if self.conn is not None:
            return self.conn

        if self.backend == "postgres":
            if psycopg is None:
                raise RuntimeError(
                    "PostgreSQL support requires psycopg. Install requirements.txt first."
                )
            if not self.database_url:
                raise RuntimeError("DATABASE_URL is required when DB_BACKEND=postgres.")
            self.conn = psycopg.connect(self.database_url, row_factory=dict_row)
        else:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row

        self._ensure_schema()
        return self.conn

    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def _ensure_schema(self):
        cursor = self.conn.cursor()
        for statement in self._schema_statements():
            cursor.execute(statement)
        self.conn.commit()

    def select(self, sql: str):
        cursor = self.connect().cursor()
        cursor.execute(sql)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def select_one(self, sql: str):
        cursor = self.connect().cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def update(self, table: str, values: dict, where: dict):
        placeholder = self._placeholder()
        set_clause = ", ".join(f"{key}={placeholder}" for key in values)
        where_clause = " AND ".join(f"{key}={placeholder}" for key in where)
        params = [self._normalize_value(value) for value in values.values()]
        params.extend(self._normalize_value(value) for value in where.values())
        self.connect().cursor().execute(
            f"UPDATE {table} SET {set_clause} WHERE {where_clause}",
            params,
        )
        self.conn.commit()

    def insert_values_by_cols(self, table: str, columns: list[str], rows: list[dict]):
        if not rows:
            return
        placeholders = ", ".join(self._placeholder() for _ in columns)
        col_expr = ", ".join(columns)
        values = [
            tuple(self._normalize_value(row.get(column)) for column in columns)
            for row in rows
        ]
        self.connect().cursor().executemany(
            self._insert_sql(table, col_expr, placeholders),
            values,
        )
        self.conn.commit()

    def insert_from_data_frame(self, table: str, df, replace: str = "INSERT IGNORE"):
        if df.empty:
            return

        records = df.where(df.notna(), None).to_dict(orient="records")
        columns = list(records[0].keys())
        placeholders = ", ".join(self._placeholder() for _ in columns)
        col_expr = ", ".join(columns)
        normalized = replace.strip().upper()
        insert_sql = self._insert_sql(
            table,
            col_expr,
            placeholders,
            ignore_conflicts="IGNORE" in normalized,
        )

        values = [
            tuple(self._normalize_value(record.get(column)) for column in columns)
            for record in records
        ]
        self.connect().cursor().executemany(
            insert_sql,
            values,
        )
        self.conn.commit()

    def _schema_statements(self):
        if self.backend == "postgres":
            return [
                """
                CREATE TABLE IF NOT EXISTS glassnode_1h (
                    id BIGSERIAL PRIMARY KEY,
                    t BIGINT NOT NULL,
                    v DOUBLE PRECISION,
                    dt TIMESTAMP NOT NULL,
                    coin TEXT NOT NULL,
                    item TEXT NOT NULL,
                    UNIQUE (coin, item, dt)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS glassnode_1d (
                    id BIGSERIAL PRIMARY KEY,
                    t BIGINT NOT NULL,
                    v DOUBLE PRECISION,
                    dt TIMESTAMP NOT NULL,
                    coin TEXT NOT NULL,
                    item TEXT NOT NULL,
                    UNIQUE (coin, item, dt)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS glassnode_json_1d (
                    id BIGSERIAL PRIMARY KEY,
                    t BIGINT NOT NULL,
                    v TEXT NOT NULL,
                    dt TIMESTAMP NOT NULL,
                    coin TEXT NOT NULL,
                    item TEXT NOT NULL,
                    UNIQUE (coin, item, dt)
                )
                """,
            ]

        return [
            """
            CREATE TABLE IF NOT EXISTS glassnode_1h (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                t INTEGER NOT NULL,
                v REAL,
                dt TEXT NOT NULL,
                coin TEXT NOT NULL,
                item TEXT NOT NULL,
                UNIQUE(coin, item, dt)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS glassnode_1d (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                t INTEGER NOT NULL,
                v REAL,
                dt TEXT NOT NULL,
                coin TEXT NOT NULL,
                item TEXT NOT NULL,
                UNIQUE(coin, item, dt)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS glassnode_json_1d (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                t INTEGER NOT NULL,
                v TEXT NOT NULL,
                dt TEXT NOT NULL,
                coin TEXT NOT NULL,
                item TEXT NOT NULL,
                UNIQUE(coin, item, dt)
            )
            """,
        ]

    def _placeholder(self):
        return "%s" if self.backend == "postgres" else "?"

    def _insert_sql(self, table: str, columns: str, placeholders: str, ignore_conflicts: bool = True):
        if self.backend == "postgres":
            suffix = " ON CONFLICT DO NOTHING" if ignore_conflicts else ""
            return f"INSERT INTO {table} ({columns}) VALUES ({placeholders}){suffix}"

        prefix = "INSERT OR IGNORE" if ignore_conflicts else "INSERT"
        return f"{prefix} INTO {table} ({columns}) VALUES ({placeholders})"

    @staticmethod
    def _row_to_dict(row):
        if row is None:
            return None
        return row if isinstance(row, dict) else dict(row)

    @staticmethod
    def _normalize_value(value):
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(value, date):
            return value.isoformat()

        if type(value).__name__ == "NaTType":
            return None

        if hasattr(value, "item") and not isinstance(value, (str, bytes)):
            try:
                return value.item()
            except (TypeError, ValueError):
                pass

        return value
