from __future__ import annotations

from data_acquisition_common import build_required_manifest, ensure_dirs, DOCS_DIR


def main() -> None:
    ensure_dirs()
    frame = build_required_manifest()
    path = DOCS_DIR / "data_manifest_required.csv"
    frame.to_csv(path, index=False)
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
