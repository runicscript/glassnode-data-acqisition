from config import HEADLESS, credentials_configured
from glassnode_v2 import ZSScraper


def main():
    if not credentials_configured():
        raise RuntimeError(
            "Please update .env with your real GLASSNODE_ACCOUNT and GLASSNODE_PASSWORD before running the scraper."
        )
    scraper = ZSScraper(headless=HEADLESS)
    scraper.main()


if __name__ == "__main__":
    main()
