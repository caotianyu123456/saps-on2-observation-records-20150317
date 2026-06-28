from __future__ import annotations

from data_acquisition_common import DOCS_DIR, build_local_manifest, build_missing_manifest, build_required_manifest, ensure_dirs, queue_frame


def main() -> None:
    ensure_dirs()
    missing = build_missing_manifest(build_required_manifest(), build_local_manifest())
    path = DOCS_DIR / "download_queue_indices.csv"
    queue_frame(missing, "indices").to_csv(path, index=False)
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
