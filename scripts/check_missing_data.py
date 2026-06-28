from __future__ import annotations

from data_acquisition_common import (
    DOCS_DIR,
    build_event_data_availability,
    build_local_manifest,
    build_missing_manifest,
    build_required_manifest,
    ensure_dirs,
    write_data_gap_report,
)


def main() -> None:
    ensure_dirs()
    required = build_required_manifest()
    local = build_local_manifest()
    missing = build_missing_manifest(required, local)
    availability = build_event_data_availability(local)
    missing_path = DOCS_DIR / "data_manifest_missing.csv"
    missing.to_csv(missing_path, index=False)
    report = write_data_gap_report(missing, availability)
    print(f"Saved {missing_path}")
    print(f"Saved {report}")


if __name__ == "__main__":
    main()
