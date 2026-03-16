from datetime import datetime

from config import GLASSNODE_ACCOUNT, GLASSNODE_PASSWORD, IS_LOCAL, PROXY_PORT, TIMEZONE


ZONEINFO = TIMEZONE


def str2ts(dstr: str) -> int:
    return int(datetime.strptime(dstr, "%Y%m%d").replace(tzinfo=ZONEINFO).timestamp())


def ts2str(ts: int) -> str:
    return datetime.fromtimestamp(ts).astimezone(ZONEINFO).strftime("%Y-%m-%d 00:00:00")


__all__ = [
    "GLASSNODE_ACCOUNT",
    "GLASSNODE_PASSWORD",
    "IS_LOCAL",
    "PROXY_PORT",
    "ZONEINFO",
    "str2ts",
    "ts2str",
]
