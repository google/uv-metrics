# MLFlow Query Tutorial

This directory contains a tutorial for combining UV's MLFlowReporter with
[MLFlow's](https://mlflow.org) query capabilities to perform multiple runs under a
single experiment umbrella, then search these results to generate plots and
perform data analysis.

Please note that this tutorial requires the `matplotlib` and `numpy` packages.

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

More information on MLFlow tracking can be found
[here](https://mlflow.org/docs/latest/tracking.html).

This tutorial also demonstrates how to use mlflow's query capabilities to
search your run data and retrieve metric history data for analysis and
plotting outside of the mlflow ui server.

In the `tutorial.py` code, in the `_run_experiments` method, you can
see that we perform several runs using different parameters. Here we configure
our MLFlow experiment name and our run name using the UV method `uv.start_run`:

```python
def _run_experiments(experiment_name: str):
  for i, p in enumerate(PARAMETERS):
    with uv.start_run(
        experiment_name=experiment_name,
        run_name=f'run_{i}',
    ):
      uv.report_params(p)
      _compute(**p)
```

You may also specify the experiment name using the `MLFLOW_EXPERIMENT_NAME`
environment variable, and the run name using the `MLFLOW_RUN_NAME` environment
variable. For more information, please see the
[MLFlow documentation](https://www.mlflow.org/docs/latest/python_api/mlflow.html#mlflow.start_run)
for more details. Please note that the method arguments take precedence over the
environment variables, so you can always set them in your code and be sure that
these will be used.

After we have run our data generation code in the `_run_experiments()` call in
the `main()` routine, we query a subset of our runs by first creating an
[MLFLow client](https://mlflow.org/docs/latest/python_api/mlflow.tracking.html#mlflow.tracking.MlflowClient)
instance, then using that to call `search_runs` to find just
the runs we are interested in:

```python
  client = mlflow.tracking.MlflowClient()
  experiment = client.get_experiment_by_name(experiment_name)

  # get all of our runs where we set mean=0
  mean_zero_runs = client.search_runs(
      experiment_ids=[experiment.experiment_id],
      filter_string='params.mean = "0"',
  )
```

Here we pass an MLFlow query string, which has a SQL-like syntax. For more details
on this query language, please see the
[MLFlow documentation](https://www.mlflow.org/docs/latest/search-syntax.html).

Once we have the runs that match our query, we retrieve our metric data and convert
it into numpy arrays for analysis and plotting, using the `get_metric_history`
MlflowClient method. As a simple example we then use `matplotlib` to plot this
simple data and output it to a `.png` file.
