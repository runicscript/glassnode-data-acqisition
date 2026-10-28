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

## BTC-First Run Profiles

To avoid running every configured metric on day one, `main.py` now supports target profiles.

- `btc_min`: `BTC_nupl_1h`, `BTC_nupl_1d`, `BTC_mvrv_1h`, `BTC_mvrv_1d`, `BTC_funding_rate_1h`
- `btc_ceo_core`: `BTC_puell_1d`, `BTC_mvrv_1d`, `BTC_asopr_1d`, `BTC_reserve_risk_1d`
- `btc_cycle_heat_core`: `BTC_fear_greed_1d`, `BTC_rhodl_ratio_1d`, `BTC_supply_1y_pct_1d`, `BTC_supply_pr_relative_1d`
- `btc_crowding_stress_core`: `BTC_funding_rate_1h`, `BTC_nupl_1h`, `BTC_mvrv_1h`
- `btc_holder_pressure_core`: `BTC_asopr_1h`, `BTC_nrpl_1h`, `BTC_sth_nupl_1h`, `BTC_sth_mvrv_1h`
- `btc_exchange_pressure_core`: `BTC_inflow_1h`, `BTC_balance_1h`, `BTC_net_transfer_1h`
- `btc_distribution_pressure_core`: raw inputs for `crowding_stress`, `holder_pressure`, and `exchange_pressure`, used to rebuild the higher-order BTC distribution-pressure composite
- `btc_valuation_stretch_core`: `BTC_mvrv_1d`, `BTC_asopr_1d`, `BTC_rhodl_ratio_1d`, `BTC_fear_greed_1d`

Preview targets without scraping:

```bash
python3 main.py --profile btc_min --dry-run-targets
```

Run BTC minimum profile:

```bash
python3 main.py --profile btc_min
```

Optional fine-grained filters:

```bash
python3 main.py --profile all --coins BTC --items nupl,mvrv --timeframes 1h,1d
```

Composite maintenance:

```bash
python3 main.py --dry-run-targets --composite-items ceo --coins BTC
python3 main.py --profile btc_ceo_core --coins BTC --composite-items ceo
python3 main.py --composite-only --composite-items ceo --coins BTC
python3 main.py --profile btc_cycle_heat_core --coins BTC --composite-items cycle_heat
python3 main.py --composite-only --composite-items cycle_heat --coins BTC
python3 main.py --profile btc_crowding_stress_core --coins BTC --composite-items crowding_stress
python3 main.py --composite-only --composite-items crowding_stress --coins BTC
python3 main.py --profile btc_holder_pressure_core --coins BTC --composite-items holder_pressure
python3 main.py --composite-only --composite-items holder_pressure --coins BTC
python3 main.py --profile btc_exchange_pressure_core --coins BTC --composite-items exchange_pressure
python3 main.py --composite-only --composite-items exchange_pressure --coins BTC
python3 main.py --profile btc_distribution_pressure_core --coins BTC --composite-items holder_pressure,exchange_pressure,crowding_stress,distribution_pressure
python3 main.py --composite-only --composite-items distribution_pressure --coins BTC

python3 main.py --profile btc_valuation_stretch_core --coins BTC --composite-items valuation_stretch
python3 main.py --composite-only --composite-items valuation_stretch --coins BTC
```

Notes:

- `--timeframes` accepts `1h`, `1d`, and `24h` (`24h` maps to `1d`).
- If filters produce zero targets, the runner exits with an explicit error.
- `--composite-items` selects derived indicators such as `ceo`.
- `--composite-only` rebuilds derived indicators directly from the current database state and does not require a browser login.
- `holder_pressure` currently tolerates isolated 1h source holes by carrying forward the previous source value for one bar only; this avoids lookahead while keeping the persisted composite gap-free.

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
