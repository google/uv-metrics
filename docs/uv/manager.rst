Measurement Manager
==========

While reporters in `uv-metrics` handle values that have already been measured,
the `MeasurementManager` feature allows you to schedule certain measurements to
run at specified intervals (which may be different for each measurement), and
automatically report the results.

A `MeasurementManager` object holds a `reporter`, which it will use to report
the measurements it makes.  To initialize a `MeasurementManager`, one passes
a reporter and a dictionary containing items which are necessary to make the
measurements (e.g., the test dataset), e.g.:

.. code-block:: python

    # make reporter
    reporter = reporters.build_reporters()

    # make static state dictionary
    static_state = {'test_set': test_dset}

    # initialize manager
    oscilloscope = manager.MeasurementManager(static_state, reporter)

Once the `MeasurementManager` is initialized, you must then tell it which
measurements to make, and at what interval to make them.  The measurement is
specified by a dictionary with keys `name`, `interval`, and `function`.  Here
`name` is a string specifying the measurement name; the `interval` is an
integer that specifies the spacing, in steps, between subsequent measurements,
and the `function` is a function which can perform a measurement given a state
dictionary.  For example:

.. code-block:: python

    oscilloscope.add_measurement({'name': 'l2_norm',
                                  'interval': 10,
                                  'function': lambda state: l2norm(state['params']}))

Then, during training, we can call the `process` function, but we need to pass
the objects needed for measurements which vary during traning, e.g.

.. code-block:: python

    for step in training_steps:
        optimizer_state = do_train_step()

        current_dict = {'params': optimizer_state.params}
        oscilloscope.process(step, current_dict)

If we want to force a measurement when it wouldn't ordinarily be measured, we
can use the `trigger_subset` method as follows

.. code-block:: python

    oscilloscope.trigger_subset(step, current_dict, ['test_acc']
Indices and tables
==================

* :ref:`search`
