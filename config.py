import os
import shutil
from pathlib import Path
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
ENV_FILE = BASE_DIR / ".env"


def load_dotenv(path: Path):
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_dotenv(ENV_FILE)


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int = 0) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def default_browser_path() -> str:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return ""


TIMEZONE = ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Shanghai"))
IS_LOCAL = env_flag("IS_LOCAL", True)
PROXY_PORT = env_int("PROXY_PORT", 0)
HEADLESS = env_flag("HEADLESS", True)
RUN_FOREVER = env_flag("RUN_FOREVER", False)

GLASSNODE_ACCOUNT = os.getenv("GLASSNODE_ACCOUNT", "")
GLASSNODE_PASSWORD = os.getenv("GLASSNODE_PASSWORD", "")
BROWSER_PATH = os.getenv("BROWSER_PATH", default_browser_path())

SQLITE_PATH = os.getenv("SQLITE_PATH", str(DATA_DIR / "glassnode.db"))
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DB_BACKEND = os.getenv("DB_BACKEND", "postgres" if DATABASE_URL else "sqlite").strip().lower()


def credentials_configured() -> bool:
    placeholders = {"", "your_email@example.com", "your_password"}
    return GLASSNODE_ACCOUNT not in placeholders and GLASSNODE_PASSWORD not in placeholders
