# Ranges that share a day are reported as not overlapping

overlaps(1, 3, 3, 5) returns False; the ranges share day 3, expected True.
