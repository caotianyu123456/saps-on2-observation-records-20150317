from pathlib import Path

import matplotlib.pyplot as plt
import netCDF4
import numpy as np


ROOT = Path(__file__).resolve().parent
FILES = {
    "16 Mar 2015": ROOT / "timed_guvi_l3-on2_2015075_Av0100r000.nc",
    "17 Mar 2015": ROOT / "timed_guvi_l3-on2_2015076_Av0100r000.nc",
}


def read_raw(path):
    ds = netCDF4.Dataset(path)
    doy = np.asarray(ds.variables["FRACTIONAL_DOY"][:], dtype=float)
    on2 = np.asarray(ds.variables["ON2"][:], dtype=float)
    lat = np.asarray(ds.variables["LATITUDE"][:], dtype=float)
    lon = np.asarray(ds.variables["LONGITUDE"][:], dtype=float)
    sza = np.asarray(ds.variables["SOLAR ZENITH ANGLE"][:], dtype=float)
    ds.close()
    ut = (doy % 1.0) * 24.0
    lt = (ut + lon / 15.0) % 24.0
    valid = np.isfinite(on2) & (np.abs(on2) < 1e20) & np.isfinite(lat) & np.isfinite(lon)
    return {"ut": ut, "lt": lt, "lat": lat, "lon": lon, "on2": on2, "sza": sza, "valid": valid}


def main():
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 8.2), dpi=220, sharex=True, sharey=True)

    for ax, (label, path) in zip(axes, FILES.items()):
        raw = read_raw(path)
        mask = raw["valid"] & (np.abs(raw["lat"]) >= 35) & (np.abs(raw["lat"]) <= 80)
        target = mask & (raw["lat"] >= 40) & (raw["lat"] <= 70) & (raw["lt"] >= 12) & (raw["lt"] <= 18)
        south = mask & (raw["lat"] >= -70) & (raw["lat"] <= -40) & (raw["lt"] >= 12) & (raw["lt"] <= 18)

        sc = ax.scatter(
            raw["lt"][mask],
            raw["lat"][mask],
            c=raw["on2"][mask],
            s=9,
            cmap="viridis",
            vmin=0,
            vmax=1.1,
            linewidths=0,
            alpha=0.86,
        )
        ax.fill_between([12, 18], 40, 70, color="#d62728", alpha=0.12)
        ax.plot([12, 18, 18, 12, 12], [40, 40, 70, 70, 40], color="#d62728", lw=2.2)
        ax.text(12.2, 67.5, f"target: 12-18 LT,\n40-70N\nn={int(target.sum())}", color="#8b0000", fontsize=9, va="top")

        ax.plot([12, 18, 18, 12, 12], [-70, -70, -40, -40, -70], color="#ff7f0e", lw=1.8, ls="--")
        ax.text(12.2, -43, f"SH 40-70S\nn={int(south.sum())}", color="#9a4f00", fontsize=9, va="top")

        ax.set_title(f"{label}: raw GUVI O/N2 observed-LT coverage")
        ax.set_ylabel("Geographic latitude (deg)")
        ax.grid(alpha=0.22)
        cbar = fig.colorbar(sc, ax=ax, pad=0.012)
        cbar.set_label("O/N2")

    axes[-1].set_xlim(0, 24)
    axes[-1].set_ylim(-80, 80)
    axes[-1].set_xticks(np.arange(0, 25, 3))
    axes[-1].set_xlabel("Observed local time of GUVI retrieval (hour)")
    fig.suptitle("TIMED/GUVI O/N2 Coverage for 12-18 LT Subauroral Sector", y=0.985, fontsize=14)
    fig.text(
        0.015,
        0.012,
        "The red box is the requested northern subauroral 12-18 LT sector. "
        "Valid 12-18 LT retrievals on these days occur only in the Southern Hemisphere/high-latitude sector.",
        ha="left",
        va="bottom",
        fontsize=8.5,
    )
    fig.tight_layout(rect=[0, 0.035, 1, 0.96])
    out = ROOT / "guvi_on2_observed_lt_12_18_coverage_check.png"
    fig.savefig(out)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()
