from time import sleep, time
from datetime import datetime
import pandas as pd
import numpy as np
from json import dumps

from scraper import Scraper
from config import (
    GLASSNODE_ACCOUNT,
    GLASSNODE_PASSWORD,
    HEADLESS,
    RUN_FOREVER,
    credentials_configured,
)
from consts import ts2str, str2ts

pd.set_option('display.max_columns', None)
pd.options.mode.chained_assignment = None

class ZSScraper(Scraper):
    def __init__(self, headless=False):
        self.name = 'ZS'
        super().__init__(self.name, db_configs='zscope', headless=headless)
        self.from_time = 0

        self.to_do_list = []
        self.interval_seconds = 3600
        self.last_update = 0

        self.computed_items = None

        self.old_in_db_map = {}

        # excluded = ['ARPA', 'ATA', 'DUSK', 'NEAR', 'NULS', 'RUNE', 'XVS']

        self.path_lookup = {
            'price': {
                'path': 'market/price_usd_close',
                'a': ['BTC', 'ETH'],
                'i': ['1h', '24h'],
                'query': {
                    'referrer': 'charts',
                }
            },
            'inflow': {
                'mutable': 1,
                'path': 'transactions/transfers_volume_to_exchanges_sum',
                # 'a': ['BTC', 'ETH'],
                'a': ['1INCH', 'AAVE', 'ACH', 'ACX', 'AGLD', 'ALICE', 'ALPHA', 'ANKR', 'APE', 'API3', 'ARKM', 'ARPA', 'ATA', 'AUCTION', 'AVA', 'AXL', 'AXS', 'BADGER', 'BAL', 'BAND', 'BAT', 'BEL', 'BICO', 'BIGTIME', 'BLUR', 'BNT', 'BTC', 'C98', 'CAKE', 'CELR', 'CHESS', 'CHR', 'CHZ', 'COMBO', 'COMP', 'COTI', 'COW', 'CRV', 'CTSI', 'DAR', 'DEGO', 'DENT', 'DIA', 'ENA', 'ENJ', 'ENS', 'ETH', 'ETHFI', 'FET', 'FTM', 'FXS', 'GALA', 'GHST', 'GLM', 'GRT', 'HFT', 'HOT', 'ID', 'ILV', 'IMX', 'INJ', 'IOTX', 'LDO', 'LEVER', 'LINA', 'LINK', 'LIT', 'LOKA', 'LPT', 'LQTY', 'LRC', 'MAGIC', 'MANA', 'MKR', 'MTL', 'NKN', 'NMR', 'OGN', 'OM', 'OMG', 'OXT', 'PEOPLE', 'PERP', 'POL', 'POWR', 'QNT', 'RARE', 'RDNT', 'REEF', 'RLC', 'RPL', 'RSR', 'SAND', 'SFP', 'SKL', 'SNX', 'SSV', 'STG', 'STMX', 'STORJ', 'SUPER', 'SUSHI', 'SYN', 'TLM', 'UMA', 'UNI', 'USDC', 'USDT', 'VIDT', 'VIRTUAL', 'WAXP', 'WLD', 'WOO', 'YFI', 'YGG', 'ZRX'],
                'i': ['1h'],
                'query': {
                    'e': 'aggregated',
                    'referrer': 'charts',
                }
            },
            'balance': {
                'mutable': 1,
                'path': 'distribution/balance_exchanges',
                # 'a': ['BTC', 'ETH', 'USDC', 'USDT'],
                'a': ['1INCH', 'AAVE', 'ACH', 'ACX', 'AGLD', 'ALICE', 'ALPHA', 'ANKR', 'APE', 'API3', 'ARKM', 'ARPA', 'ATA', 'AUCTION', 'AVA', 'AXL', 'AXS', 'BADGER', 'BAL', 'BAND', 'BAT', 'BEL', 'BICO', 'BIGTIME', 'BLUR', 'BNT', 'BTC', 'C98', 'CAKE', 'CELR', 'CHESS', 'CHR', 'CHZ', 'COMBO', 'COMP', 'COTI', 'COW', 'CRV', 'CTSI', 'DAR', 'DEGO', 'DENT', 'DIA', 'ENA', 'ENJ', 'ENS', 'ETH', 'ETHFI', 'FET', 'FTM', 'FXS', 'GALA', 'GHST', 'GLM', 'GRT', 'HFT', 'HOT', 'ID', 'ILV', 'IMX', 'INJ', 'IOTX', 'LDO', 'LEVER', 'LINA', 'LINK', 'LIT', 'LOKA', 'LPT', 'LQTY', 'LRC', 'MAGIC', 'MANA', 'MKR', 'MTL', 'NKN', 'NMR', 'OGN', 'OM', 'OMG', 'OXT', 'PEOPLE', 'PERP', 'POL', 'POWR', 'QNT', 'RARE', 'RDNT', 'REEF', 'RLC', 'RPL', 'RSR', 'SAND', 'SFP', 'SKL', 'SNX', 'SSV', 'STG', 'STMX', 'STORJ', 'SUPER', 'SUSHI', 'SYN', 'TLM', 'UMA', 'UNI', 'USDC', 'USDT', 'VIDT', 'VIRTUAL', 'WAXP', 'WLD', 'WOO', 'YFI', 'YGG', 'ZRX'],


                'i': ['1h'],
                'query': {
                    'e': 'aggregated',
                    'referrer': 'charts',
                }
            },
            'price_realized': {
                'path': 'market/price_realized_usd',
                'a': ['BTC'],
                'i': ['1h'],
            },
            'nupl': {
                'path': 'indicators/net_unrealized_profit_loss',
                'a': ['BTC', 'ETH'],
                'i': ['1h', '24h'],
                'query': {
                    'referrer': 'charts',
                }
            },
            'nrpl': {
                'path': 'indicators/net_realized_profit_loss',
                'a': ['BTC'],
                'i': ['1h', '24h'],
                'query': {
                    'referrer': 'charts',
                }
            },
            'sth_nupl': {
                'path': 'indicators/nupl_less_155',
                'a': ['BTC', 'ETH'],
                'i': ['1h'],
                'query': {
                    'referrer': 'charts',
                }
            },
            'mvrv': {
                'path': 'market/mvrv',
                'a': ['BTC', 'ETH'],
                'i': ['1h', '24h'],
                'query': {
                    'referrer': 'charts',
                }
            },
            'sth_mvrv': {
                'path': 'market/mvrv_less_155',
                'a': ['BTC'],
                'i': ['1h'],
                'query': {
                    'referrer': 'charts',
                }
            },
            'net_transfer': {
                'mutable': 1,
                'path': 'transactions/transfers_volume_exchanges_net',
                'a': ['BTC', 'ETH', 'USDT', 'USDC'],
                'i': ['1h'],
                'query': {
                    'e': 'aggregated',
                    'referrer': 'charts',
                }
            },
            'fear_greed': {
                'path': 'indicators/fear_greed',
                'a': ['BTC'],
                'i': ['24h'],
                'query': {
                    'referrer': 'charts',
                },
                'advanced': 1,
            },
            'puell': {
                'path': 'indicators/puell_multiple',
                'a': ['BTC'],
                'i': ['24h'],
                'query': {
                    'referrer': 'charts',
                }
            },
            'asopr': {
                'path': 'indicators/sopr_adjusted',
                'a': ['BTC'],
                'i': ['1h', '24h'],
                'query': {
                    'referrer': 'charts',
                }
            },
            'reserve_risk': {
                'path': 'indicators/reserve_risk',
                'a': ['BTC'],
                'i': ['24h'],
            },
            'rhodl_ratio': {
                'path': 'indicators/rhodl_ratio',
                'a': ['BTC'],
                'i': ['24h'],
            },
            'funding_rate': {
                'path': 'derivatives/futures_funding_rate_perpetual_v2',
                'a': ['BTC', 'ETH'],
                'i': ['1h'],
                'query': {
                    'e': 'aggregated',
                    'referrer': 'charts',
                }
            },
            'supply': {
                'path': 'supply/current',
                'a': ['BTC', 'ETH'],
                'i': ['24h'],
                'query': {
                    'referrer': 'charts',
                }
            },
            'supply_1y_pct': {
                # 与supply相乘后使用，乘积出现急涨急跌后，等待低点高点做多或空
                'path': 'supply/active_more_1y_percent',
                'a': ['BTC'],
                'i': ['24h'],
                'query': {
                    'referrer': 'charts',
                },
            },
            'supply_pr_relative': {
                'path': 'supply/profit_relative',
                'a': ['BTC', 'ETH'],
                'i': ['24h'],
                'query': {
                    'referrer': 'charts',
                }
            },
            'urpd': {
                'path': 'indicators/utxo_realized_price_distribution_ath',
                'a': ['BTC'],
                'i': ['24h'],
                'query': {
                    'referrer': 'charts',
                },
                'json': 1,
                'del_last': 1
            }
        }

    def login(self):
        page = self.page
        if page.mode == 's':
            page.change_mode(go=False)
        self.log('Logining')
        # url = "https://www.glassnode.com"
        url = "https://studio.glassnode.com/auth/login"
        # url = "https://auth.glassnode.com/login?state=hKFo2SA1Nk92X2ZXYUdyWFJkeVU5ZENzbXZGUExlS3BheWxCOKFupWxvZ2luo3RpZNkgSnVuLWNrQzFrSHJvWVktVFZWQXJMNUxGci1sTnNOSlmjY2lk2SBNNXNUOThWVDRGVXJRTm4xcDk2VmVUblIyaVRyNnFvdQ&client=M5sT98VT4FUrQNn1p96VeTnR2iTr6qou&protocol=oauth2&prompt=login&scope=openid%20profile%20email%20offline_access&audience=https%3A%2F%2Fapi.glassnode.com&redirect_uri=https%3A%2F%2Fstudio.glassnode.com%2Fsuccess&response_type=code&response_mode=query&nonce=a0R4bDdHWDkuRV9%2Bbkl0eTVJbzNsVEw3d1VfN2RfUkgyLlpTRExPN1JIdw%3D%3D&code_challenge=yXNuqnkh5OMJ8l-e0ZiEA1AUeG4ixzG-QoiNFZbn9EQ&code_challenge_method=S256&auth0Client=eyJuYW1lIjoiYXV0aDAtcmVhY3QiLCJ2ZXJzaW9uIjoiMi4wLjEifQ%3D%3D"
        try:
            page.get(url)
            # print(page.user_agent)
            # page.ele('Sign in').click()
            sleep(.5)
            if not GLASSNODE_ACCOUNT or not GLASSNODE_PASSWORD:
                raise ValueError('Missing GLASSNODE_ACCOUNT or GLASSNODE_PASSWORD')
            page.ele('#email').input(GLASSNODE_ACCOUNT)
            sleep(.5)
            page.ele('#current-password').input(GLASSNODE_PASSWORD)
            sleep(.5)
            page.ele('Continue').click()
            for i in range(10):
                sleep(1)
                print(page.url)
                res = page.response
                if res:
                    print(res.status_code, res.text)
                if 'home' in page.url:
                    break

        except:
            self.exception('Login Failed')
            sleep(10)
            self.login()

    def get_gn_data(self, url):
        self.page.change_mode('s', go=False)
        # self.log(url)
        try:
            self.page.get(url, timeout=120)
            res = self.page.response
            # res = requests.get(url, headers=self.headers,
            #                    proxies=self.proxies)
            # res = requests.post(url, json=data, headers=headers, proxies={"http": 'http://127.0.0.1:4780/', "https": 'http://127.0.0.1:4780/'})
            if res is None:
                sleep(10)
                return None

            if res.status_code == 200:
                return res.json()
            elif res.status_code == 403 or res.status_code == 401:
                self.log(res.text)
                self.login()
                self.page.change_mode('s', go=False)
                return self.get_gn_data(url)
            else:
                self.log(f'{res.status_code} {self.page.raw_data}')
                raise Exception(res.text)
        except (ConnectionResetError, ConnectionError) as e:
            self.log(f'{e}, 5秒后重试')
            sleep(5)
            return self.get_gn_data(url)

    @staticmethod
    def to_second(v, delta):
        return int((v if len(str(v)) < 13 else v / 1000) - delta)

    def get_ceo(self, coin='BTC'):
        self.db.connect()

        sql = f"SELECT max(dt) AS max_dt FROM glassnode_1d WHERE item='ceo' AND coin='{coin}'"
        row = self.db.select_one(sql)
        if row is None:
            max_ts = self.str2ts('20150101')
        else:
            max_ts = self.dt2ts(row['max_dt'])

        days_4y = 365 * 4
        start_ts = max_ts - 86400 * (days_4y + 40)
        sql = f"""SELECT dt,
                MAX(CASE WHEN item = 'puell' THEN v ELSE NULL END) AS puell,
                MAX(CASE WHEN item = 'mvrv' THEN v ELSE NULL END) AS mvrv,
                MAX(CASE WHEN item = 'asopr' THEN v ELSE NULL END) AS asopr,
                MAX(CASE WHEN item = 'reserve_risk' THEN v ELSE NULL END) AS reserve_risk
            FROM
                glassnode_1d
            WHERE coin = 'BTC' AND dt >= '{self.ts2str(start_ts)}'
            GROUP BY dt ORDER BY dt
        """

        rows = self.db.select(sql)
        df = pd.DataFrame(rows)
        df = df.dropna()
        df = df.set_index('dt')

        df['m2-1'] = df['mvrv'] - 1
        roll_m2 = df['m2-1'].rolling(window=days_4y)
        m2_mean = roll_m2.mean()
        m2_std = roll_m2.std()
        df['m2_upper'] = m2_mean + m2_std
        df['m2_lower'] = m2_mean - m2_std * 0.8
        # df['m2_upper'], df['m2_middle'], df['m2_lower'] = BBANDS(df['m2-1'], 4 * 365, 1, 0.8)
        df['f3'] = np.where(df['m2-1'] > df['m2_upper'], 1, np.where(df['m2-1'] < df['m2_lower'], -1, 0))

        df['m6-1'] = df['asopr'].ewm(span=30, adjust=False).mean() - 1
        # df['m6_upper'], df['m6_middle'], df['m6_lower'] = BBANDS(df['m6-1'], 4 * 365, 1, 0.7)
        roll_m6 = df['m6-1'].rolling(window=days_4y)
        m6_mean = roll_m6.mean()
        m6_std = roll_m6.std()
        df['m6_upper'] = m6_mean + m6_std
        df['m6_lower'] = m6_mean - m6_std * 0.7
        df['f4'] = np.where(df['m6-1'] > df['m6_upper'], 1, np.where(df['m6-1'] < df['m6_lower'], -1, 0))

        df['m3'] = df['puell'].rolling(window=7).mean()
        df['m3-1'] = df['m3'] - 1
        # df['m3_upper'], df['m3_middle'], df['m3_lower'] = BBANDS(df['m3-1'], 4 * 365, 1, 0.7)
        roll_m3 = df['m3-1'].rolling(window=days_4y)
        m3_mean = roll_m3.mean()
        m3_std = roll_m3.std()
        df['m3_upper'] = m3_mean + m3_std
        df['m3_lower'] = m3_mean - m3_std * 0.7
        df['f5'] = np.where(df['m3-1'] > df['m3_upper'], 1, np.where(df['m3-1'] < df['m3_lower'], -1, 0))

        # df['f7'] = df['price'] / df['price'].rolling(window=200).mean()

        df['f8'] = df['reserve_risk'] / df['reserve_risk'].rolling(window=365).mean() - 1

        # df['f8_upper'], df['f8_middle'], df['f8_lower'] = BBANDS(df['f8'], 4 * 365, 1, 0.8)
        roll_f8 = df['f8'].rolling(window=days_4y)
        f8_mean = roll_f8.mean()
        f8_std = roll_f8.std()
        f8_upper = f8_mean + f8_std
        f8_lower = f8_mean - f8_std * 0.8
        df['f6'] = np.where(df['f8'] > f8_upper, 1, np.where(df['f8'] < f8_lower, -1, 0)) * 0.5

        # 图形上的系数先乘后除可以不用
        df['v'] = (df['f3'] + df['f4'] + df['f5'] + df['f6']).ewm(span=7, adjust=False).mean() / 4

        # print(df['dt'].iloc[-1], data[-1])
        df = df.loc[self.ts2str(max_ts):]
        df = df[['v']]
        df['coin'] = coin
        df['item'] = 'ceo'
        df = df.reset_index()
        # print(df.tail())
        self.db.insert_from_data_frame('glassnode_1d', df, replace='INSERT IGNORE')
        self.log(f'{coin} ceo success: {df.iloc[-1]["dt"]}')

        df = None


    def validate_gn(self, tf):
        print('validating ' + tf)
        self.db.connect()

        sql = f"SELECT coin, item FROM glassnode_{tf} GROUP BY coin, item"
        rows = self.db.select(sql)
        interval = 3600 if tf == '1h' else 86400
        for row in rows:
            coin = row['coin']
            item = row['item']
            print(coin, item)
            data = self.db.select(f'SELECT * FROM glassnode_{tf} WHERE coin="{coin}" AND item="{item}" AND dt >= "2024-05-01 00:00:00" ORDER BY t')
            df = pd.DataFrame(data)

            last_ts = df.iloc[0]['t']
            for index, _row in df.iloc[1:].iterrows():
                if _row['t'] - last_ts > interval:
                    self.log(f"{coin}_{item} {_row['dt']} has gap {_row['t'] - last_ts}")
                    break
                last_ts = _row['t']

        self.db.close()

    def parse_gn_data(self, indicator, data):
        if indicator == 'urpd':
            return [{
                't': d['t'],
                'v': dumps({
                    'ath': d['ath_price'],
                    'current': d['current_price'],
                    'd': d['partitions'],
                    'supply': d['total_supply'],
                })
            } for d in data]

    def update_gn(self, to_update=set()):
        # self.login()
        self.page.change_mode('s', go=False)
        self.db.connect()

        not_updated = set()
        for indicator, options in self.path_lookup.items():
            # query = '&'.join(f"{key}={value}" for key, value in lookup['params'].items())
            base_url = f"https://api.glassnode.com/v1/metrics/{options['path']}?"
            for asset in options['a']:
                for interval in options['i']:
                    # if interval == '24h' and hour != 8:
                    #     continue

                    tf = "1d" if interval == "24h" else "1h"

                    hash_id = f"{asset}_{indicator}_{tf}"

                    if to_update and hash_id not in to_update:
                        continue

                    # if hash_id != 'ETH_sth_nupl_1h':
                    #     continue

                    max_ts = self.max_ts.get(hash_id, 0)

                    gap = 3600 if interval == '1h' else 86400

                    expected_ts = (int(time()) // gap - 1) * gap

                    if max_ts >= expected_ts:
                    # if max_ts // gap == int(time()) // gap - 1:
                        self.log(f"{hash_id} is up to date")
                        continue

                    query = options.get('query', {}).copy()
                    query['c'] = 'native'

                    query['a'] = asset
                    query['i'] = interval
                    start_t = self.max_t.get(hash_id, 0)
                    if start_t:
                        query['s'] = start_t - 3600 * 50 if 'mutable' in options else start_t
                    keys = sorted(query.keys())
                    parsed = []
                    for key in keys:
                        parsed.append(f"{key}={query[key]}")
                    parsed = '&'.join(parsed)

                    url = f'{base_url}{parsed}'
                    try:
                        data = self.get_gn_data(url)

                        if data is None:
                            self.log(f"{hash_id} failed to get data from {url}")
                            not_updated.add(hash_id)
                            continue

                        # if 'del_last' in options:
                        #     data = data[:-1]

                        delta = gap if 'advanced' in options else 0

                        max_t = data[-1]['t']

                        if self.to_second(max_t, delta) > expected_ts:
                            data = data[:-1]
                            max_t = data[-1]['t']
                            if indicator != 'urpd':
                                self.warn(f"{indicator}: {hash_id} {max_t} is ahead of expected {expected_ts}")

                        if max_t > start_t:
                            self.max_ts[hash_id] = self.to_second(max_t, delta)
                            self.max_t[hash_id] = max_t

                            if 'json' in options:
                                data = self.parse_gn_data(indicator, data)
                                table = f'glassnode_json_{tf}'
                            else:
                                table = f'glassnode_{tf}'

                            df = pd.DataFrame(data)
                            df = df.dropna()

                            if len(str(data[0]['t'])) < 13:
                                unit = 's'
                            else:
                                print(hash_id, 'ms')
                                unit = 'ms'

                            new = df[df['t'] > start_t].copy()

                            new['coin'] = asset
                            new['item'] = indicator
                            new['dt'] = pd.to_datetime(new['t'] - delta, unit=unit, origin='1970-01-01 08:00:00')

                            # print(df['dt'].iloc[-1], data[-1])
                            self.db.insert_from_data_frame(table, new, replace='INSERT IGNORE')
                            self.log(f'{hash_id} success: {new.iloc[-1]["dt"]}')
                            # if hash_id in to_update:
                            #     to_update.remove(hash_id)

                            for computed_item, units in self.computed_items.items():
                                if hash_id in units:
                                    units.remove(hash_id)
                                    if not units:
                                        # del self.computed_items[computed_item]
                                        getattr(self, 'get_' + computed_item)()

                            if 'mutable' in options:
                                old_in_db = self.old_in_db_map.get(hash_id)
                                old = df[df['t'] <= start_t]
                                if old_in_db:
                                    for index, row in old.iterrows():
                                        ts = row['t']
                                        dbv = old_in_db.get(ts)
                                        if dbv and abs(row['v'] - dbv) > 0.0001:
                                            dt = ts2str(ts)
                                            self.log(f'{hash_id} muted after {round((time() - ts - 3600) / 60)} minutes: {dt} {dbv} -> {row["v"]}')
                                            self.db.update(table, {'v': row['v']}, {
                                                'dt': dt,
                                                'coin': asset,
                                                'item': indicator
                                            })

                                old_in_db = {}
                                for index, row in old.iterrows():
                                    old_in_db[row['t']] = row['v']
                                self.old_in_db_map[hash_id] = old_in_db


                        else:
                            # self.log(f'{hash_id} not updated: {max_t} {start_t} {expected_ts}')
                            not_updated.add(hash_id)

                        sleep(2.88)

                    except:
                        self.exception(f'{indicator} {asset} {interval} failed')
                        break

        if not_updated:
            if datetime.now().minute < 30:
                sleep(10)
                self.log(f'重新update: {not_updated}')
                self.update_gn(not_updated)
                return
            else:
                self.warn(f'超时未更新：{not_updated}')
        self.db.close()

    def main(self):
        self.run_once()

        if not RUN_FOREVER:
            return

        while True:
            ts = time()
            wait = 3600 - ts % 3600 + 5
            self.log(f"sleep {wait} seconds")
            sleep(wait)
            self.run_once()

    def run_once(self):
        self.db.connect()
        tables = ['glassnode_1h', 'glassnode_1d', 'glassnode_json_1d']
        self.max_t = {}
        self.max_ts = {}
        for table in tables:
            tf = table[-2:]
            sql = f"SELECT max(t) AS max_t, coin, item FROM {table} GROUP BY coin, item"
            rows = self.db.select(sql)

            for row in rows:
                opts = self.path_lookup.get(row['item'], {})
                key = f"{row['coin']}_{row['item']}_{tf}"
                t = row['max_t']
                if 'advanced' in opts:
                    delta = 3600 if tf == '1h' else 86400
                else:
                    delta = 0
                self.max_t[key] = t
                self.max_ts[key] = self.to_second(t, delta)

        self.db.close()

        if 1:
            self.computed_items = {
                'ceo': ['BTC_puell_1d', 'BTC_mvrv_1d', 'BTC_asopr_1d', 'BTC_reserve_risk_1d']
            }
            self.update_gn()


if __name__ == "__main__":
    if not credentials_configured():
        raise RuntimeError(
            "Please update .env with your real GLASSNODE_ACCOUNT and GLASSNODE_PASSWORD before running the scraper."
        )
    scraper = ZSScraper(headless=HEADLESS)
    scraper.main()

#
"""
# m1: price
m2: mvrv ratio = price / price_realized
m3: puell multiple
m4: Reserve Risk ?
m5: RHODL Ratio ?
m6: asopr
f3 = (if(m2-1,">",sma(m2-1,4*365)+std(m2-1,4*365),1,0)    -   if(m2-1,"<",sma(m2-1,4*365)- 0.8*std(m2-1,4*365),1,0)    ) * 1.0
f4 = (if(m6-1,">",sma(m6-1,4*365)+std(m6-1,4*365),1,0)    -   if(m6-1,"<",sma(m6-1,4*365)- 0.7*std(m6-1,4*365),1,0)    )  * 0.75
f5 = (if(m3-1,">",sma(m3-1,4*365)+std(m3-1,4*365),1,0)    -   if(m3-1,"<",sma(m3-1,4*365)- 0.7*std(m3-1,4*365),1,0)    ) * 0.5
f6 = (if(f8,">",sma(f8,4*365)+std(f8,4*365),1,0)    -   if(f8,"<",sma(f8,4*365)- 0.8*std(f8,4*365),1,0)    ) * 0.5 * 0.25
# f7: Mayer Multiple = m1/sma(m1,200)
f8: Adjusted Reserve Risk = m4/sma(m4,365) -1
condition_sum = ema((f3+f4/0.75+f5/0.5+f6/0.25),7) / 4

"""
# import numpy as np
# # 24h
# df = pd.DataFrame()
# df['m2-1'] = df['mvrv'] - 1
# df['m2_upper'], df['m2_middle'], df['m2_lower'] = BBANDS(df['m2-1'], 4 * 365, 1, 0.8)
# df['f3'] = np.where(df['m2-1'] > df['m2_upper'], 1, np.where(df['m2-1'] < df['m2_lower'], -1, 0))
#
# df['m6-1'] = df['asopr'] - 1
# df['m6_upper'], df['m6_middle'], df['m6_lower'] = BBANDS(df['m6-1'], 4 * 365, 1, 0.7)
# df['f4'] = np.where(df['m6-1'] > df['m6_upper'], 1, np.where(df['m6-1'] < df['m6_lower'], -1, 0))
#
# df['m3-1'] = df['puell'] - 1
# df['m3_upper'], df['m3_middle'], df['m3_lower'] = BBANDS(df['m3-1'], 4 * 365, 1, 0.7)
# df['f5'] = np.where(df['m3-1'] > df['m3_upper'], 1, np.where(df['m3-1'] < df['m3_lower'], -1, 0))
#
# df['f7'] = df['price'] / df['price'].rolling(window=200).mean()
#
# df['f8'] = df['reserve_risk'] / df['reserve_risk'].rolling(window=365) - 1
#
# df['f8_upper'], df['f8_middle'], df['f8_lower'] = BBANDS(df['f8'], 4 * 365, 1, 0.8)
# df['f6'] = np.where(df['f8-1'] > df['f8_upper'], 1, np.where(df['f8'] < df['f8_lower'], -1, 0)) * 0.5
#
# df['condition_sum'] = EMA(df['f3'] + df['f4'] + df['f5'] + df['f6'], 7) / 4

# {'t': 1721692800, 'v': 2.1133794880675443}, {'t': 1721779200, 'v': 2.0941975779199185}]
