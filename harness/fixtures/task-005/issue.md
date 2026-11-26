# Negative business-day offsets go the wrong way

add_business_days(date(2026, 1, 5), -1) returns Tuesday Jan 6 — it went forward; Monday Jan 5 minus one business day is Friday Jan 2.
