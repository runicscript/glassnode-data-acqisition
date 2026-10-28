import argparse
from typing import Iterable

from config import HEADLESS, credentials_configured
from glassnode_v2 import ZSScraper


PROFILE_TARGETS: dict[str, list[str]] = {
    "btc_min": [
        "BTC_nupl_1h",
        "BTC_nupl_1d",
        "BTC_mvrv_1h",
        "BTC_mvrv_1d",
        "BTC_funding_rate_1h",
    ],
    "btc_ceo_core": [
        "BTC_puell_1d",
        "BTC_mvrv_1d",
        "BTC_asopr_1d",
        "BTC_reserve_risk_1d",
    ],
    "btc_cycle_heat_core": [
        "BTC_fear_greed_1d",
        "BTC_rhodl_ratio_1d",
        "BTC_supply_1y_pct_1d",
        "BTC_supply_pr_relative_1d",
    ],
    "btc_crowding_stress_core": [
        "BTC_funding_rate_1h",
        "BTC_nupl_1h",
        "BTC_mvrv_1h",
    ],
    "btc_holder_pressure_core": [
        "BTC_asopr_1h",
        "BTC_nrpl_1h",
        "BTC_sth_nupl_1h",
        "BTC_sth_mvrv_1h",
    ],
    "btc_exchange_pressure_core": [
        "BTC_inflow_1h",
        "BTC_balance_1h",
        "BTC_net_transfer_1h",
    ],
    "btc_distribution_pressure_core": [
        "BTC_funding_rate_1h",
        "BTC_nupl_1h",
        "BTC_mvrv_1h",
        "BTC_asopr_1h",
        "BTC_nrpl_1h",
        "BTC_sth_nupl_1h",
        "BTC_sth_mvrv_1h",
        "BTC_inflow_1h",
        "BTC_balance_1h",
        "BTC_net_transfer_1h",
    ],
    "btc_valuation_stretch_core": [
        "BTC_mvrv_1d",
        "BTC_asopr_1d",
        "BTC_rhodl_ratio_1d",
        "BTC_fear_greed_1d",
    ],
}


def _parse_csv_arg(value: str | None, *, upper: bool = False) -> set[str]:
    if not value:
        return set()
    raw_values = [item.strip() for item in value.split(",")]
    cleaned = {item for item in raw_values if item}
    if upper:
        return {item.upper() for item in cleaned}
    return cleaned


def _normalize_timeframes(values: set[str]) -> set[str]:
    normalized: set[str] = set()
    for value in values:
        parsed = value.lower()
        if parsed == "24h":
            parsed = "1d"
        if parsed not in {"1h", "1d"}:
            raise ValueError(
                f"Unsupported timeframe '{value}'. Use 1h, 1d, or 24h."
            )
        normalized.add(parsed)
    return normalized


def _expand_all_targets(scraper: ZSScraper) -> set[str]:
    targets: set[str] = set()
    for indicator, options in scraper.path_lookup.items():
        assets = options.get("a", [])
        intervals = options.get("i", [])
        for asset in assets:
            for interval in intervals:
                timeframe = "1d" if interval == "24h" else "1h"
                targets.add(f"{asset}_{indicator}_{timeframe}")
    return targets


def _expand_all_composite_targets(scraper: ZSScraper) -> set[str]:
    return set(scraper.list_composite_targets())


def _parse_target_parts(target: str) -> tuple[str, str, str]:
    prefix, timeframe = target.rsplit("_", 1)
    coin, item = prefix.split("_", 1)
    return coin, item, timeframe


def _filter_targets(
    *,
    targets: Iterable[str],
    coins: set[str],
    items: set[str],
    timeframes: set[str],
) -> set[str]:
    filtered: set[str] = set()
    for target in targets:
        coin, item, timeframe = _parse_target_parts(target)
        if coins and coin not in coins:
            continue
        if items and item not in items:
            continue
        if timeframes and timeframe not in timeframes:
            continue
        filtered.add(target)
    return filtered


def _resolve_targets(scraper: ZSScraper, args: argparse.Namespace) -> tuple[set[str], int]:
    all_targets = _expand_all_targets(scraper)
    if args.profile == "all":
        selected = set(all_targets)
    else:
        selected = set(PROFILE_TARGETS[args.profile])
        missing = sorted(selected - all_targets)
        if missing:
            raise RuntimeError(
                "Profile contains targets that are not present in current path_lookup: "
                + ", ".join(missing)
            )

    coins = _parse_csv_arg(args.coins, upper=True)
    items = _parse_csv_arg(args.items, upper=False)
    timeframes = _normalize_timeframes(_parse_csv_arg(args.timeframes, upper=False))

    selected = _filter_targets(
        targets=selected,
        coins=coins,
        items=items,
        timeframes=timeframes,
    )
    if not selected:
        raise RuntimeError(
            "No targets matched the current filters. Try a broader profile/filter set."
        )
    return selected, len(all_targets)


def _resolve_composite_targets(
    scraper: ZSScraper,
    args: argparse.Namespace,
) -> tuple[set[str], int]:
    all_targets = _expand_all_composite_targets(scraper)
    composite_items = _parse_csv_arg(args.composite_items, upper=False)
    coins = _parse_csv_arg(args.coins, upper=True)
    timeframes = _normalize_timeframes(_parse_csv_arg(args.timeframes, upper=False))

    selected = _filter_targets(
        targets=all_targets,
        coins=coins,
        items=composite_items,
        timeframes=timeframes,
    )
    if not selected:
        raise RuntimeError(
            "No composite targets matched the current filters. Try a broader composite filter set."
        )
    return selected, len(all_targets)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Glassnode collector runner with profile and target filters."
    )
    parser.add_argument(
        "--profile",
        choices=["all", *sorted(PROFILE_TARGETS)],
        default="all",
        help="Target profile. Use btc_min for BTC-first bootstrap.",
    )
    parser.add_argument(
        "--coins",
        help="Optional coin filter, comma-separated. Example: BTC,ETH",
    )
    parser.add_argument(
        "--items",
        help="Optional indicator item filter, comma-separated. Example: nupl,mvrv",
    )
    parser.add_argument(
        "--timeframes",
        help="Optional timeframe filter, comma-separated. Supports 1h,1d,24h.",
    )
    parser.add_argument(
        "--dry-run-targets",
        action="store_true",
        help="Print resolved target list and exit without running scraper.",
    )
    parser.add_argument(
        "--composite-items",
        help="Optional composite item filter, comma-separated. Example: ceo",
    )
    parser.add_argument(
        "--composite-only",
        action="store_true",
        help="Skip raw Glassnode scraping and recompute the selected composite items from the current database state.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    requires_browser = not args.composite_only and not args.dry_run_targets
    if requires_browser and not credentials_configured():
        raise RuntimeError(
            "Please update .env with your real GLASSNODE_ACCOUNT and GLASSNODE_PASSWORD before running the scraper."
        )
    scraper = ZSScraper(headless=HEADLESS, browser_enabled=requires_browser)
    composite_targets, all_composite_target_count = _resolve_composite_targets(scraper, args)

    if args.composite_only:
        targets = set()
        all_target_count = 0
    else:
        targets, all_target_count = _resolve_targets(scraper, args)

    if args.dry_run_targets:
        if targets:
            print(f"Resolved {len(targets)} raw targets (from {all_target_count} total):")
            for target in sorted(targets):
                print(target)
        else:
            print("Resolved 0 raw targets (composite-only mode).")
        print(
            f"Resolved {len(composite_targets)} composite targets "
            f"(from {all_composite_target_count} total):"
        )
        for target in sorted(composite_targets):
            print(target)
        return

    force_recompute_composites = bool(args.composite_items or args.composite_only)

    if args.composite_only:
        print(
            f"Recomputing {len(composite_targets)} composite targets "
            f"(from {all_composite_target_count} total)."
        )
    else:
        print(f"Running {len(targets)} raw targets (from {all_target_count} total).")
        if force_recompute_composites:
            print(
                f"Forcing recompute for {len(composite_targets)} composite targets "
                f"(from {all_composite_target_count} total)."
            )
        else:
            print(
                f"Auto-maintaining {len(composite_targets)} composite targets "
                f"(from {all_composite_target_count} total)."
            )
    scraper.main(
        to_update=targets if targets else None,
        composite_targets=composite_targets,
        force_recompute_composites=force_recompute_composites,
        composite_only=args.composite_only,
    )


if __name__ == "__main__":
    main()
