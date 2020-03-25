## 0.4.0

- on TensorboardReporter, pushed the default max_queue up to 100.
- Removed f-strings so that we stay compatible with Python 3.5.2 and up.
- Fixed a bug in `LoggingReporter` where logging numpy objects would fail.
- added `report_each_n` method to reporters; this is a convenience method that
  causes the reporter to only report when the `step % n == 0`.

## 0.3.0

First real release, available on Artifactory!
