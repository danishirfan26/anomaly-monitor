import unittest

from monitor import detect, synthetic_readings


class MonitorTests(unittest.TestCase):
    def test_warmup_and_quarantine(self):
        alerts = list(detect([5, 5, 5, 20, -20, 5], window=3, scale_floor=1))
        self.assertEqual([alert.index for alert in alerts], [3, 4])
        self.assertEqual([alert.baseline for alert in alerts], [5, 5])

    def test_future_readings_do_not_change_existing_alerts(self):
        values = [2, 2, 2, 20, 2]
        self.assertEqual(
            list(detect(values, window=3)),
            [alert for alert in detect(values + [50, 90], window=3) if alert.index < len(values)],
        )

    def test_rejects_nonfinite_readings(self):
        with self.assertRaises(ValueError):
            list(detect([2, 2, float("nan")], window=3))

    def test_default_synthetic_incidents(self):
        values, incidents = synthetic_readings()
        self.assertEqual({alert.index for alert in detect(values)}, incidents)


if __name__ == "__main__":
    unittest.main()
