from __future__ import annotations

from data_acquisition_common import write_core_manifests


def main() -> None:
    required, local, missing, availability = write_core_manifests()
    print(f"Saved required manifest rows: {len(required)}")
    print(f"Saved local manifest rows: {len(local)}")
    print(f"Saved missing manifest rows: {len(missing)}")
    print(f"Saved event availability rows: {len(availability)}")


if __name__ == "__main__":
    main()
