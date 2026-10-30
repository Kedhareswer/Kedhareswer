"""Self-check for the streak maths: python scripts/test_build.py"""
import datetime as dt
from build import streaks

today = dt.date(2026, 10, 31)
day = lambda n: today - dt.timedelta(days=n)
assert streaks({}, today) == (0, 0)
assert streaks({day(0): 1, day(1): 2, day(2): 1}, today) == (3, 3)
assert streaks({day(1): 1, day(2): 1}, today) == (2, 2)  # today not committed yet keeps the streak
assert streaks({day(2): 1, day(10): 1, day(11): 1, day(12): 1}, today) == (0, 3)
print("ok")
