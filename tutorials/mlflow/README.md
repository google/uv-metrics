# MLFlowReporter Tutorial

This directory contains a very simple demo of using UV's MLFLowReporter to log metrics
to an [MLFLow](https://mlflow.org) backend.

To run this tutorial:

```
python3 tutorial.py
```

By default, this will create a directory `./mlruns` in your current folder and store
your metrics data there. To view the results in your browser, you can run an
`mlflow ui` instance in your current folder:

```
mlflow ui
```

By default this will serve results at `http://localhost:5000`.

You can change the mlflow experiment and run names by setting the environment
variables `MLFLOW_EXPERIMENT_NAME` and `MLFLOW_RUN_NAME`, respectively, or you can set
them in the `uv.start_run()` method. You can also use an existing MLFlow tracking
server by setting the `MLFLOW_TRACKING_URI` environment variable.

More information on MLFlow tracking can be found
[here](https://mlflow.org/docs/latest/tracking.html).
