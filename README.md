# Glassnode Data Collector

This project keeps the Glassnode scraping logic from the original scripts and replaces the missing private modules with local ones.

## Files

- `main.py`: entry point
- `glassnode_v2.py`: Glassnode metric collection logic
- `scraper.py`: browser/session wrapper
- `config.py`: environment-based settings
- `db.py`: local SQLite storage wrapper
- `logger.py`: standard logging wrapper

## Quick Start

1. Create a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` or export the environment variables manually.
4. Run `python3 main.py`.

If Chromium is not detected automatically, set `BROWSER_PATH` in `.env`.

## Current Storage

The project currently uses SQLite through `db.py` so the scraper can run without the original private database module. This is a good local stepping stone before moving to a managed cloud database.

## Switch To Cloud Postgres

1. Create a managed PostgreSQL database.
2. Put its connection string in `DATABASE_URL`.
3. Set `DB_BACKEND=postgres`.
4. Run the scraper again. The tables are created automatically.

You can test the database connection first with `python3 check_db.py`.

## Railway Deploy

This project is ready to deploy to Railway with the included `Dockerfile`.

### 1. Push to GitHub

Push this folder to a GitHub repository.

### 2. Create a Railway service

In Railway:

1. Create a new project.
2. Choose `Deploy from GitHub repo`.
3. Select this repository.
4. Railway will detect the `Dockerfile` and build from it.

### 3. Add Railway variables

Set these variables in Railway:

- `GLASSNODE_ACCOUNT`
- `GLASSNODE_PASSWORD`
- `DB_BACKEND=postgres`
- `DATABASE_URL=your Supabase session pooler URI`
- `HEADLESS=true`
- `IS_LOCAL=false`
- `APP_TIMEZONE=Asia/Shanghai`

Optional:

- `RUN_FOREVER=false`
- `BROWSER_PATH=/usr/bin/chromium`

Do not upload your local `.env` file to GitHub.

### 4. Verify the deployment

For a normal service, Railway will run:

```bash
python main.py
```

You can also temporarily run:

```bash
python check_db.py
```

to verify database connectivity inside Railway.

### 5. Convert it to a Cron Job

Because `main.py` runs once and exits, it fits Railway Cron Jobs well.

In Railway, configure the service as a Cron Job and use a schedule like:

```text
5 * * * *
```

That runs the scraper once per hour, five minutes after the hour.
