# Recently read keys get evicted

With capacity 2: put a, put b, read a, then put c — a is evicted even though it was just used; b should have been evicted.
