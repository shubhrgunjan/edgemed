"""Opt-in numeric timings: never retain queries, records, or credentials."""

import time
from contextlib import contextmanager


@contextmanager
def span(timings, name):
    start = time.perf_counter_ns()
    try:
        yield
    finally:
        if timings is not None:
            timings[name] = timings.get(name, 0.0) + (time.perf_counter_ns() - start) / 1e6
