from __future__ import annotations

from data_acquisition_common import write_normalization_status


def main() -> None:
    print(f"Saved {write_normalization_status('indices')}")


if __name__ == "__main__":
    main()
