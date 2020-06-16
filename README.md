# UV Metrics

[![Build status](https://img.shields.io/travis/google/uv-metrics/master.svg?maxAge=3600)](http://travis-ci.org/google/uv-metrics)
[![Codecov branch](https://img.shields.io/codecov/c/github/google/uv-metrics/master.svg?maxAge=3600)](https://codecov.io/github/google/uv-metrics)
[![readthedocs](https://img.shields.io/readthedocs/uv-metrics?maxAge=3600)](https://uv-metrics.readthedocs.io/en/latest/?badge=latest)
[![Latest version](https://img.shields.io/pypi/v/uv-metrics?maxAge=3600)](https://pypi.org/project/uv-metrics)

`uv-metrics` is a Python library that makes it easy to instrument your machine
learning workflows, report those metrics to a variety of storage backends, and
analyze those metrics in a notebook or script.

UV is designed to work in or out of a Dockerized environment. It was designed
alongside [Caliban](https://github.com/google/caliban), and interacts nicely
with Caliban's job history management features to make metrics easier than ever.

## Installation and Usage

Install UV Metrics via [pip](https://pypi.org/project/uv-metrics/):

```bash
pip install uv-metrics
```

Full documentation for UV lives at [Read The
Docs](https://uvmetrics.readthedocs.io/en/latest).

## Disclaimer

This is a research project, not an official Google product. Expect bugs and
sharp edges. Please help by trying out UV, [reporting
bugs](https://github.com/google/uv-metrics/issues), and letting us know what you
think!

## Citing UV Metrics

If UV Metrics helps you in your research, pleae consider citing the repository:

```
@software{uv2020github,
  author = {Sam Ritchie},
  title = {{UV Metrics}: Metric reporting and experiment management for ML workflows.},
  url = {http://github.com/google/uv-metrics},
  version = {0.1.0},
  year = {2020},
}
```

In the above bibtex entry, names are in alphabetical order, the version number
is intended to be that of the latest tag on github, and the year corresponds to
the project's open-source release.

## License

Copyright 2020 Google LLC.

Licensed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).
