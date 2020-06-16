## 0.4.0

- bumped the minimum python version back up to 3.6.
- SQLReader and SQLReporter; these work like other persistent stores, but work
  with local SQLite databases.
- on TensorboardReporter, pushed the default max_queue up to 100.
- Removed f-strings so that we stay compatible with Python 3.5.2 and up.
- Fixed a bug in `LoggingReporter` where logging numpy objects would fail.
- added `report_each_n` method to reporters; this is a convenience method that
  causes the reporter to only report when the `step % n == 0`.
- Added a `digits` arguments to `LoggingReporter` that allows you to print more
  digits in the output.
- Added `CASReader`, a reader implementation that can pull items from an
  instance of CASFS.
- Added a function that can copy metrics directories into a CASFS instance
  located anywhere.

## 0.3.0

First release.
