MLFlow Reporting
================

UV supports reporting to an `MLFlow <https://mlflow.org>`_ backend via the
`uv.mlflow.reporter.MLFlowReporter` class. Using this reporter, you can
easily log your parameters, tags, and metrics to a local directory or to your
existing MLFlow backend:

.. code-block:: python

  import uv
  from uv.mlflow.reporter import MLFlowReporter

  def train(steps: int, slope: float):
    for i in range(steps):
      uv.report(step=i, k='my_metric', v=i*slope)

  def main(**kwargs):
    with uv.start_run(), uv.active_reporter(MLFlowReporter()):
      uv.report_params(kwargs)
      train(**kwargs)

  main(steps=8, slope=1.0)

Here we can see the steps needed to set up and use an `MLFlowReporter`. We
start an `MLFlow run <https://mlflow.org/docs/latest/tracking.html#concepts>`_ using
`with uv.start_run()` so that our run will be properly closed when our code execution
is finished. Then we create an MLFlowReporter and set it as active using `uv.active_reporter()`.
Once we have done this, we are ready to store parameters and log metrics to our MLFlow backend.

By default, this will create a directory `./mlruns` in your current folder and store
your metrics data there. To view the results in your browser, you can run an
`mlflow ui` instance in your current folder:

.. code-block:: shell-session

  mlflow ui

By default, this serves results at `http://localhost:5000`. Open this page in your browser
and you should be able to view the results of your run.

You can change the MLFlow experiment and run names by setting the environment
variables `MLFLOW_EXPERIMENT_NAME` and `MLFLOW_RUN_NAME`, respectively, or you can set
the `experiment_name` and `run_name` parameters  in the `uv.start_run()` method. You can
also use an existing MLFlow tracking server by setting the `MLFLOW_TRACKING_URI` environment
variable.

Please see our `mlflow tutorial code <https://github.com/google/uv-metrics/tree/master/tutorials/mlflow>`_
for a complete example.

For a more involved example that uses `Caliban <https://github.com/google/caliban>`_ to
build Docker images and integrate with an existing MLFlow SQL-based backend, see
`this tutorial <https://github.com/google/caliban/tree/master/tutorials/uv-metrics>`_.
