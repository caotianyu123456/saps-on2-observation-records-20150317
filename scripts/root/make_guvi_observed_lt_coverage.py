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
    orbit = np.asarray(ds.variables["ORBIT"][:], dtype=float)
    ds.close()

    ut = (doy % 1.0) * 24.0
    lt = (ut + lon / 15.0) % 24.0
    valid = np.isfinite(on2) & (np.abs(on2) < 1e20) & np.isfinite(lat) & np.isfinite(lon)
    return {"ut": ut, "lt": lt, "lat": lat, "lon": lon, "on2": on2, "sza": sza, "orbit": orbit, "valid": valid}


def summarize(label, raw):
    print(label)
    for name, mask in [
        ("NH 40-70N", raw["valid"] & (raw["lat"] >= 40) & (raw["lat"] <= 70)),
        ("SH 40-70S", raw["valid"] & (raw["lat"] >= -70) & (raw["lat"] <= -40)),
    ]:
        target = mask & (raw["lt"] >= 18) & (raw["lt"] <= 24)
        print(f"  {name}: all n={int(mask.sum())}, LT18-24 n={int(target.sum())}")
        if mask.any():
            print(
                "    observed LT {:.2f}-{:.2f}, UT {:.2f}-{:.2f}, SZA {:.1f}-{:.1f}, median O/N2 {:.3f}".format(
                    np.nanmin(raw["lt"][mask]),
                    np.nanmax(raw["lt"][mask]),
                    np.nanmin(raw["ut"][mask]),
                    np.nanmax(raw["ut"][mask]),
                    np.nanmin(raw["sza"][mask]),
                    np.nanmax(raw["sza"][mask]),
                    np.nanmedian(raw["on2"][mask]),
                )
            )


def main():
    data = {label: read_raw(path) for label, path in FILES.items()}
    for label, raw in data.items():
        summarize(label, raw)

    fig, axes = plt.subplots(2, 1, figsize=(10.5, 8.2), dpi=220, sharex=True, sharey=True)
    for ax, (label, raw) in zip(axes, data.items()):
        mask = raw["valid"] & (np.abs(raw["lat"]) >= 35) & (np.abs(raw["lat"]) <= 75)
        sc = ax.scatter(
            raw["lt"][mask],
            raw["lat"][mask],
            c=raw["on2"][mask],
            s=9,
            cmap="viridis",
            vmin=0,
            vmax=1.1,
            linewidths=0,
            alpha=0.88,
        )
        ax.fill_between([18, 24], 40, 70, color="#d62728", alpha=0.11, step="post")
        ax.plot([18, 24, 24, 18, 18], [40, 40, 70, 70, 40], color="#d62728", lw=2.2)
        ax.text(18.2, 67.5, "target: 18-24 LT,\n40-70N", color="#8b0000", fontsize=9, va="top")
        ax.axhline(40, color="0.35", lw=0.8, ls=":")
        ax.axhline(70, color="0.35", lw=0.8, ls=":")
        ax.axvline(18, color="0.35", lw=0.8, ls=":")
        ax.axvline(24, color="0.35", lw=0.8, ls=":")
        ax.set_title(f"{label}: raw GUVI O/N2 valid points in subauroral latitudes")
        ax.set_ylabel("Geographic latitude (deg)")
        ax.grid(alpha=0.22)
        cbar = fig.colorbar(sc, ax=ax, pad=0.012)
        cbar.set_label("O/N2")

    axes[-1].set_xlim(0, 24)
    axes[-1].set_ylim(-75, 75)
    axes[-1].set_xticks(np.arange(0, 25, 3))
    axes[-1].set_xlabel("Observed local time of GUVI retrieval (hour)")
    fig.suptitle("TIMED/GUVI O/N2 Observed Local-Time Coverage Check", y=0.985, fontsize=14)
    fig.text(
        0.015,
        0.012,
        "The red box marks the requested northern subauroral dusk/night sector. "
        "No valid raw GUVI O/N2 retrievals fall inside 18-24 LT and 40-70N on either day.",
        ha="left",
        va="bottom",
        fontsize=8.5,
    )
    fig.tight_layout(rect=[0, 0.035, 1, 0.96])
    out = ROOT / "guvi_on2_observed_lt_coverage_check.png"
    fig.savefig(out)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()
