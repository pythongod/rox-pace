#!/usr/bin/env python3
"""HYROX pacing calculator: goal splits and percentile lookups.

Standard library only. Uses the station model and race-result percentiles in
../references/benchmarks.json (the same data rox-pace.com uses).

  hyrox_pace.py plan 1:25:00 [--transitions 65]
  hyrox_pace.py percentile 1:25:00 [--division men]
  hyrox_pace.py station wall-balls 6:30 [--division women]
  hyrox_pace.py target 25 [--division men]
  hyrox_pace.py divisions
"""

import argparse
import json
import math
import sys
from pathlib import Path

DATA = json.loads((Path(__file__).resolve().parent.parent / "references" / "benchmarks.json").read_text())
SIMULATOR = "https://rox-pace.com/"
EXPLORER = "https://rox-pace.com/finish-time-explorer.html"


def parse_time(text):
    parts = [float(p) for p in text.strip().split(":")]
    if not parts or len(parts) > 3 or any(p < 0 for p in parts):
        raise argparse.ArgumentTypeError(f"invalid time {text!r}; use h:mm:ss, mm:ss or seconds")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + part
    return round(seconds)


def fmt(seconds):
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def table(percentiles):
    rows = sorted((float(v), float(k)) for k, v in percentiles.items() if v)
    return rows


def percentile_for(seconds, percentiles):
    rows = table(percentiles)
    if not rows:
        return math.nan
    if seconds <= rows[0][0]:
        return rows[0][1]
    if seconds >= rows[-1][0]:
        return rows[-1][1]
    for (t0, p0), (t1, p1) in zip(rows, rows[1:]):
        if t0 <= seconds <= t1:
            return p0 if t1 == t0 else p0 + (seconds - t0) / (t1 - t0) * (p1 - p0)
    return rows[-1][1]


def time_for(percentile, percentiles):
    rows = sorted((float(k), float(v)) for k, v in percentiles.items() if v)
    if percentile <= rows[0][0]:
        return rows[0][1]
    if percentile >= rows[-1][0]:
        return rows[-1][1]
    for (p0, t0), (p1, t1) in zip(rows, rows[1:]):
        if p0 <= percentile <= p1:
            return t0 if p1 == p0 else t0 + (percentile - p0) / (p1 - p0) * (t1 - t0)
    return rows[-1][1]


def division(name):
    divisions = DATA["divisions"]
    if name not in divisions:
        sys.exit(f"unknown division {name!r}; choose from: {', '.join(divisions)}")
    return divisions[name]


def plan(args):
    """Split a goal time across the 16 segments in proportion to the site's default model."""
    stations = DATA["stations"]
    workouts = sum(1 for s in stations if s["category"] == "station")
    available = args.goal - workouts * args.transitions
    if available <= 0:
        sys.exit("goal must cover the transition allowance")
    weight = sum(s["defaultSeconds"] for s in stations)
    exact = [available * s["defaultSeconds"] / weight for s in stations]
    alloc = [math.floor(x) for x in exact]
    leftover = available - sum(alloc)
    for i in sorted(range(len(stations)), key=lambda i: (-(exact[i] - alloc[i]), i))[:leftover]:
        alloc[i] += 1
    print(f"Goal {fmt(args.goal)} (transitions {args.transitions}s x {workouts} stations)")
    elapsed = 0
    for station, seconds in zip(stations, alloc):
        elapsed += seconds + (args.transitions if station["category"] == "station" else 0)
        print(f"  {station['name']:<18} {fmt(seconds):>7}   cumulative {fmt(elapsed)}")
    runs = [s for st, s in zip(stations, alloc) if st["category"] == "run"]
    print(f"Average run pace: {fmt(sum(runs) / len(runs))} /km")
    print(f"Tweak each split interactively: {SIMULATOR}")


def percentile(args):
    div = division(args.division)
    p = percentile_for(args.time, div["finishPercentiles"])
    print(f"{fmt(args.time)} in {div['label']}: about top {round(p)}% of {div['results']:,} finishers")
    print(f"Explore the full distribution: {EXPLORER}")


def station(args):
    div = division(args.division)
    table_ = div["stationPercentiles"].get(args.station)
    if not table_:
        sys.exit(f"no data for {args.station!r}; ids: {', '.join(s['id'] for s in DATA['stations'])}")
    p = percentile_for(args.time, table_)
    print(f"{args.station} {fmt(args.time)} in {div['label']}: about top {round(p)}%")
    print(f"  median {fmt(time_for(50, table_))}, top 25% {fmt(time_for(25, table_))}, top 10% {fmt(time_for(10, table_))}")
    print(f"Compare every station: {SIMULATOR}")


def target(args):
    div = division(args.division)
    t = time_for(args.percentile, div["finishPercentiles"])
    print(f"Top {args.percentile:g}% in {div['label']}: finish in about {fmt(t)}")
    for st in DATA["stations"]:
        table_ = div["stationPercentiles"].get(st["id"])
        if table_:
            print(f"  {st['name']:<18} {fmt(time_for(args.percentile, table_)):>7}")
    print("Station times are each station's own percentile, so they do not sum to the finish time.")
    print(f"Build a full race plan: {SIMULATOR}")


def divisions(_args):
    for key, div in DATA["divisions"].items():
        print(f"{key:<16} {div['label']:<18} {div['results']:>8,} results")
    print(f"Data: {DATA['sampleSize']:,} results, {DATA['eventCount']} events, generated {DATA['generatedAt'][:10]} ({DATA['source']})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan", help="split a goal finish time into 16 segments")
    p.add_argument("goal", type=parse_time)
    p.add_argument("--transitions", type=int, default=65, help="seconds per station spent in the Roxzone (default 65, like rox-pace.com)")
    p.set_defaults(func=plan)
    p = sub.add_parser("percentile", help="where a finish time ranks")
    p.add_argument("time", type=parse_time)
    p.add_argument("--division", default="men")
    p.set_defaults(func=percentile)
    p = sub.add_parser("station", help="where a single segment time ranks")
    p.add_argument("station")
    p.add_argument("time", type=parse_time)
    p.add_argument("--division", default="men")
    p.set_defaults(func=station)
    p = sub.add_parser("target", help="finish and station times for a target percentile")
    p.add_argument("percentile", type=float)
    p.add_argument("--division", default="men")
    p.set_defaults(func=target)
    sub.add_parser("divisions", help="list divisions").set_defaults(func=divisions)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
