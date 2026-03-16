from db import DBHandler


def main():
    db = DBHandler()
    try:
        db.connect()
        row = db.select_one("SELECT CURRENT_TIMESTAMP AS now")
        print(
            {
                "status": "ok",
                "backend": db.backend,
                "server_time": row["now"] if row else None,
            }
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
