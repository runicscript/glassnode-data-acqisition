from DrissionPage import ChromiumOptions, SessionOptions, WebPage
from datetime import datetime

from config import BROWSER_PATH
from db import DBHandler
from logger import LoggerClient
from consts import IS_LOCAL, PROXY_PORT, ZONEINFO


class Scraper(LoggerClient):
    def __init__(self, name, db_configs=None, headless=False):
        self.name = name
        super().__init__(name)
        self.db = DBHandler(configs=db_configs)
        so = SessionOptions()
        co = ChromiumOptions()
        co.auto_port()

        if BROWSER_PATH:
            co.set_browser_path(BROWSER_PATH)

        print('local', IS_LOCAL)

        if IS_LOCAL:
            if headless:
                # co.set_argument('--headless')

                co.set_argument("--window-size=1920,1080")
                # co.set_argument("--disable-extensions")
                # co.set_argument("--proxy-bypass-list=*")
                # co.set_argument("--start-maximized")
                co.set_argument('--headless')
                # co.set_argument('--disable-gpu')
                # co.set_argument('--disable-dev-shm-usage')
                # co.set_argument('--no-sandbox')
                # co.set_argument('--ignore-certificate-errors')
                co.set_user_agent(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')

            if PROXY_PORT:
                so.set_proxies(http=f'127.0.0.1:{PROXY_PORT}')
        else:
            co.set_argument("--window-size=1920,1080")
            co.set_argument('--incognito')
            # co.set_argument("--disable-extensions")
            # co.set_argument("--proxy-bypass-list=*")
            # co.set_argument("--start-maximized")
            co.set_argument('--headless')
            co.set_argument('--disable-gpu')
            # co.set_argument('--disable-dev-shm-usage')
            co.set_argument('--no-sandbox')
            # co.set_argument('--ignore-certificate-errors')
            co.set_user_agent(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')

            # from DrissionPage.easy_set import set_headless, set_paths
            # set_headless(True)
            # co.set_argument('--no-sandbox')
            # co.set_argument('--headless')
            # co.set_argument('--incognito')
            # co.set_user_agent(
            #     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')
            #
            # co.set_argument("--window-size=1920,1080")
            # co.set_argument("--disable-extensions")
            # # co.set_argument("--proxy-server='direct://'")
            # # co.set_argument("--proxy-bypass-list=*")
            # # co.set_argument("--start-maximized")
            # # co.set_argument('--headless')
            # co.set_argument('--disable-gpu')
            # # co.set_argument('--disable-dev-shm-usage')
            # # co.set_argument('--no-sandbox')
            # co.set_argument('--ignore-certificate-errors')
            #
            # co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')

            # user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
            # co.set_argument(f'user-agent={user_agent}')

        self.page = WebPage(session_or_options=so, chromium_options=co)

        self.max_dt_map = None
        self.interval_seconds = 3600

    @staticmethod
    def current_dt_str():
        return datetime.now(ZONEINFO).strftime('%Y%m%d %H:%M')

    @staticmethod
    def str2ts(dstr):
        return int(datetime.strptime(dstr, '%Y%m%d').replace(tzinfo=ZONEINFO).timestamp())

    @staticmethod
    def ts2str(ts):
        return datetime.fromtimestamp(ts).astimezone(ZONEINFO).strftime('%Y-%m-%d 00:00:00')

    @staticmethod
    def dt2ts(dt):
        if isinstance(dt, str):
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                try:
                    dt = datetime.strptime(dt, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f'Unsupported datetime string: {dt}')

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZONEINFO)
        else:
            dt = dt.astimezone(ZONEINFO)
        return int(dt.replace(tzinfo=ZONEINFO).timestamp())

    @staticmethod
    def parse_big_num(raw):
        val = raw.replace('$', '').replace(',', '')
        unit = val[-1]
        if unit.isdigit():
            return val

        num = float(val[:-1])
        if unit == '亿':
            return num * 100000000
        if unit == '万':
            return num * 10000
        if unit == 'M':
            return num * 1000000
        if unit == 'B':
            return num * 1000000000

    def switch_mode(self, mode):
        if self.page.mode != mode:
            self.page.change_mode(mode, go=False)

    def session_get(self, url, home=False):
        # 先用d模式打开网页自动加载headers
        self.switch_mode('d')
        # url = "https://www.ishares.com/us/products/333011/ishares-bitcoin-trust"

        if home is None:
            home = url.replace('https://', '').split('/')[0]
        page = self.page
        page.get('https://' + home)
        print('ready')
        self.switch_mode('s')
        page.get(url)

    def ele_by_xpath(self, xpath):
        return self.page.ele(f'xpath:{xpath}')

    def eles_by_xpath(self, xpath):
        return self.page.eles(f'xpath:{xpath}')

