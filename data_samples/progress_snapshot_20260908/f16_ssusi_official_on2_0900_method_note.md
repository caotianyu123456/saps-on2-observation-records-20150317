# F16 SSUSI Official ON2 Check

Input product: DMSP/SSUSI `edr-day-limb` for F16 REV58873.

Variables used: `ON2`, `ON2_VARIANCE`, `DATA_QUALITY`, `MEAN_TANGENTPOINT_LATITUDE_GEOMAGNETIC`, and `MEAN_GEOMAGNETIC_LOCAL_TIME`.

Basic validity rule used here: `ON2 > 0`. DQ0-positive samples are counted separately, because this product can contain `DATA_QUALITY=0` rows with `ON2=0`, which are not usable O/N2 retrievals.

For the 2015-03-17 08:55:30-09:02:30 UT southern SAPS-like crossing window, the official SSUSI ON2 rows in the high-latitude southern sector all have `ON2=0`. Therefore this case cannot be upgraded to a colocated official SSUSI ON2 value at the SAPS point; the previous 135.6/LBHS result remains a radiance-ratio proxy only.
