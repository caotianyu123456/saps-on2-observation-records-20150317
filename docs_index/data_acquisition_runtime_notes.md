# Data Acquisition Runtime Notes

Updated: 2026-06-28

The uploaded data-acquisition scripts are public-safe. They do not hard-code local machine paths.

To reproduce the same local inventory behavior on another machine, configure these optional environment variables before running the scripts:

```text
SAPS_ON2_EXTERNAL_WORKSPACE=/path/to/SAPS_SAR_arcs_or_equivalent_workspace
SAPS_ON2_DMSP_DIR=/path/to/DMSP_SSIES_archive
```

If these variables are not set, the scripts look under repository-local placeholders:

```text
data_external/saps_sar_arcs
data_external/dmsp
data_raw/
```

The full local inventory file `docs_index/data_manifest_local.csv` was generated in the local workspace, but it contains machine-specific absolute paths. For the public GitHub repository, use:

```text
docs_index/data_manifest_local_public_summary.csv
```

This public summary preserves the event/data-group coverage counts without publishing local filesystem metadata.
