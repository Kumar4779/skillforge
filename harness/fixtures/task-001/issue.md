# Durations under a minute are lost

Durations under a minute are lost: `parse_duration('45s')` returns `0` instead of `45`. Mixed values are also wrong: `'1h15s'` returns `3600` instead of `3615`.
