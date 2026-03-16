# Glassnode Data Acquisition

This project collects selected Glassnode metrics, logs into Glassnode through a browser session, fetches data from the Glassnode API, and stores the results in a PostgreSQL database.

The current setup has already been validated end-to-end:

`Glassnode login -> fetch BTC_price_1h -> write to Supabase Postgres`

## What This Project Does

- Logs into Glassnode with a browser-based session
- Fetches Glassnode metrics through the API
- Stores data in PostgreSQL
- Supports local execution
- Supports deployment to Railway
- Supports scheduled execution through Railway Cron Jobs

## Project Structure

- `main.py`
  Entry point. Runs one collection task and exits.
- `glassnode_v2.py`
  Main collection logic, including metric definitions, login flow, API requests, incremental updates, and derived metrics.
- `scraper.py`
  Browser and session wrapper.
- `db.py`
  Database layer with support for both `sqlite` and `postgres`.
- `config.py`
  Environment variable configuration loader.
- `check_db.py`
  Small utility script to verify database connectivity.
- `requirements.txt`
  Python dependencies.
- `Dockerfile`
  Railway deployment image with Chromium installed.

## Database Tables

The project automatically creates and uses these tables:

- `glassnode_1h`
- `glassnode_1d`
- `glassnode_json_1d`

## Local Setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create your environment file

```bash
cp .env.example .env
```

Then edit `.env`.

Minimum example:

```env
GLASSNODE_ACCOUNT=your_glassnode_email
GLASSNODE_PASSWORD=your_glassnode_password
HEADLESS=true
IS_LOCAL=true
DB_BACKEND=postgres
DATABASE_URL=your_postgres_connection_string
APP_TIMEZONE=Asia/Shanghai
```

If browser detection does not work locally, add:

```env
BROWSER_PATH=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
```

### 4. Test database connectivity

```bash
python3 check_db.py
```

Expected output will look similar to:

```python
{'status': 'ok', 'backend': 'postgres', 'server_time': ...}
```

### 5. Run the collector

```bash
python3 main.py
```

## Environment Variables

- `GLASSNODE_ACCOUNT`
  Glassnode login email
- `GLASSNODE_PASSWORD`
  Glassnode login password
- `HEADLESS`
  Whether to run Chromium in headless mode
- `IS_LOCAL`
  Use `true` for local runs and `false` in cloud environments
- `APP_TIMEZONE`
  Application timezone, currently recommended: `Asia/Shanghai`
- `DB_BACKEND`
  `sqlite` or `postgres`
- `SQLITE_PATH`
  Local SQLite path, only used in `sqlite` mode
- `DATABASE_URL`
  PostgreSQL connection string
- `BROWSER_PATH`
  Browser executable path
- `RUN_FOREVER`
  Whether to keep looping forever. For Railway Cron Jobs, keep this `false`.

## PostgreSQL Recommendation

Recommended database:

- Supabase Postgres

Recommended connection type:

- Use the `Session pooler` URI

Example:

```env
DATABASE_URL=postgresql://postgres.xxxxx:yourpassword@aws-1-xxx.pooler.supabase.com:5432/postgres?sslmode=require
```

Important notes:

- Use the full connection string exactly as provided
- Remove `[` and `]` if they appear around the password placeholder in the example
- Do not leave placeholders like `yourpassword` unchanged
- If your password contains special characters, URI parsing can break
- The simplest option is to use a database password with only letters and numbers

## Railway Deployment

This project is ready for Railway deployment with the included `Dockerfile`.

### 1. Push the project to GitHub

Make sure these files are ignored:

```gitignore
.env
.venv/
__pycache__/
.DS_Store
data/
```

Then push the project to GitHub.

### 2. Create a Railway project

In Railway:

1. Create a new project
2. Choose `Deploy from GitHub repo`
3. Select this repository
4. Railway will automatically detect the `Dockerfile`

### 3. Add Railway environment variables

At minimum, set:

```env
GLASSNODE_ACCOUNT=your_glassnode_email
GLASSNODE_PASSWORD=your_glassnode_password
DB_BACKEND=postgres
DATABASE_URL=your_supabase_session_pooler_uri
HEADLESS=true
IS_LOCAL=false
APP_TIMEZONE=Asia/Shanghai
RUN_FOREVER=false
BROWSER_PATH=/usr/bin/chromium
```

### 4. Start command

The default command is:

```bash
python main.py
```

### 5. Schedule it as a Cron Job

Recommended cron expression:

```text
5 * * * *
```

This runs the job once per hour, five minutes after the hour.

## Validated Functionality

The following has already been verified:

- Local Chromium initialization works
- Glassnode login works
- `BTC_price_1h` fetch works
- Data is written successfully to Supabase Postgres
- PostgreSQL tables are created automatically
- Railway deployment files are prepared

## Notes

- Do not upload `.env` to GitHub
- When creating the GitHub repository, keep README, `.gitignore`, and license set to `No`
- If Railway fails, check environment variables first
- If the database fails, run `python check_db.py` first

## Recommended Next Steps

1. Deploy the repository to Railway
2. Run it once manually
3. Confirm fresh records appear in Supabase
4. Then enable the Railway Cron Job
