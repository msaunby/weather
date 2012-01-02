#!/usr/bin/env python
#
# Purpose:
# Convert coords to/from 20th Century reanalysis grid.
#
# The grid is 94 rows of 192 cols
# Longitudes are regularly spaced,  latitudes are regular
# except when very close to poles.
# This code assumes all are regular, so will be in slight error
# near poles.


def toXY(lat,lng):
    y = ((90 - lat))/ 1.9  - 0.368
    y = 0 if y < 0 else 93 if y > 93 else y  
    x = ((lng + 0.9375)% 360) / 1.875
    return (int(x),int(y))


