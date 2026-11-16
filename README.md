# Anomaly Monitor

A causal anomaly detector for a stream of machine readings. The monitor scores each value against the rolling median and scaled median absolute deviation of earlier accepted readings, with a configurable minimum scale for quiet sensors. An alert carries its index, reading, baseline and score. The monitor keeps flagged readings out of the rolling window so one spike cannot hide the next one.

## Run

Use Python 3.10 or newer. Run from this repository with the standard library.

```sh
python monitor.py
python monitor.py --csv readings.csv --window 21 --threshold 4.5 --scale-floor 0.6
python -m unittest -v
```

The CSV needs a `value` column with one finite number per row in chronological order. Alert indices start at zero. The first window supplies the warm-up history.

## Demo result

With seed 19 the detector flagged **6 of 6** labelled spikes across 150 synthetic readings, with **zero false alerts**. Consecutive spikes at indices 31 and 32 used the same baseline. The demo includes gradual drift and isolated positive and negative spikes.

The benchmark uses deliberately large spikes. A sustained level change can keep the detector alerting against a stale baseline, and an incident during warm-up can enter the reference window. An extension would compare two safe reset strategies on a synthetic step change.

This is an AI-assisted portfolio project. The sensor readings are fictional. [NIST on median absolute deviation](https://www.itl.nist.gov/div898/handbook/eda/section3/eda356.htm)
