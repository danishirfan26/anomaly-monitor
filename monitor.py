"""Flag unusual readings in an ordered sensor stream."""

import argparse
import csv
import json
import math
import random
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import median


@dataclass(frozen=True)
class Alert:
    index: int
    value: float
    baseline: float
    score: float


def detect(values, window=21, threshold=4.5, scale_floor=0.6):
    """Use only previous accepted values to score the current reading."""
    if window < 3:
        raise ValueError("Window must contain at least three readings.")
    if not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("Threshold must be positive and finite.")
    if not math.isfinite(scale_floor) or scale_floor <= 0:
        raise ValueError("Scale floor must be positive and finite.")

    history = deque(maxlen=window)
    for index, value in enumerate(values):
        if not math.isfinite(value):
            raise ValueError(f"Reading {index} must be finite.")
        if len(history) == window:
            baseline = median(history)
            mad = median(abs(previous - baseline) for previous in history)
            scale = max(1.4826 * mad, scale_floor)
            score = abs(value - baseline) / scale
            if score >= threshold:
                yield Alert(index, value, baseline, score)
                continue
        history.append(value)


def synthetic_readings(seed=19):
    """Create a slow sensor drift with a handful of labelled spikes."""
    rng = random.Random(seed)
    spikes = {31: 8, 32: 7, 59: -9, 80: 6, 115: 8, 139: -7}
    values = [
        40 + 0.025 * index + 0.4 * math.sin(index / 4)
        + rng.gauss(0, 0.48) + spikes.get(index, 0)
        for index in range(150)
    ]
    return values, set(spikes)


def read_values(path):
    with path.open(newline="", encoding="utf-8-sig") as source:
        rows = csv.DictReader(source, strict=True)
        if not rows.fieldnames or "value" not in rows.fieldnames:
            raise ValueError("CSV requires a value column.")
        values = []
        for row in rows:
            try:
                values.append(float(row["value"]))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid value on CSV line {rows.line_num}.") from exc
    if not values:
        raise ValueError("CSV contains no readings.")
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, help="Read values in input order from a value column.")
    parser.add_argument("--seed", type=int, default=19)
    parser.add_argument("--window", type=int, default=21)
    parser.add_argument("--threshold", type=float, default=4.5)
    parser.add_argument("--scale-floor", type=float, default=0.6)
    args = parser.parse_args()
    try:
        values, incidents = (read_values(args.csv), None) if args.csv else synthetic_readings(args.seed)
        alerts = list(detect(values, args.window, args.threshold, args.scale_floor))
    except (OSError, ValueError, csv.Error) as exc:
        parser.error(str(exc))

    report = {
        "source": "csv" if args.csv else "synthetic",
        "readings": len(values),
        "warmup_readings": min(args.window, len(values)),
        "alerts": [asdict(alert) for alert in alerts],
    }
    if incidents is not None:
        flagged = {alert.index for alert in alerts}
        report["label_check"] = {
            "detected_incidents": len(flagged & incidents),
            "missed_incidents": len(incidents - flagged),
            "false_alerts": len(flagged - incidents),
        }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
