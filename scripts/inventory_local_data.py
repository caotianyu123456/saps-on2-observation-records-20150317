from __future__ import annotations

from data_acquisition_common import (
    DOCS_DIR,
    OUTPUT_DIR,
    build_event_catalog,
    build_event_data_availability,
    build_event_universe_frame,
    build_local_manifest,
    ensure_dirs,
)


def main() -> None:
    ensure_dirs()
    local = build_local_manifest()
    availability = build_event_data_availability(local)
    universe = build_event_universe_frame(local)
    catalog = build_event_catalog(local)
    local.to_csv(DOCS_DIR / "data_manifest_local.csv", index=False)
    availability.to_csv(OUTPUT_DIR / "event_data_availability.csv", index=False)
    universe.to_csv(OUTPUT_DIR / "event_universe.csv", index=False)
    catalog.to_csv(OUTPUT_DIR / "event_catalog_auto_available_dates.csv", index=False)
    print(f"Saved {DOCS_DIR / 'data_manifest_local.csv'}")
    print(f"Saved {OUTPUT_DIR / 'event_data_availability.csv'}")
    print(f"Saved {OUTPUT_DIR / 'event_universe.csv'}")
    print(f"Saved {OUTPUT_DIR / 'event_catalog_auto_available_dates.csv'}")


if __name__ == "__main__":
    main()
