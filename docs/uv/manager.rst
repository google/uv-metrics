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

    import uv.manager as m
    import uv.reporter as r

    # make reporter
    reporter = r.MemoryReporter().stepped()

    # make static state dictionary
    static_state = {'test_set': test_dset}

    # initialize manager
    oscilloscope = m.MeasurementManager(static_state, reporter)

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

Then, during training, we can call the `measure` function, but we need to pass
the objects needed for measurements which vary during traning, e.g.

.. code-block:: python

    for step in training_steps:
        optimizer_state = do_train_step()

        current_dict = {'params': optimizer_state.params}
        oscilloscope.measure(step, current_dict)

If we want to perform a measurement at any time (say outside the normal
schedule), we can use the same `measure` method, but now we must provide the
argument `measurement_list` as follows:

.. code-block:: python

    oscilloscope.measure(step, current_dict, measurement_list=['test_acc'])

This will measure, in the above case, `test_acc`, regardless of what the
corresponding measurement interval and step are.

.. warning::
    When you call `.measure()` with an explicit `measurement_list`, the manager
    will only measure those measurements in the list, and will NOT go through
    and check which measurements to perform based on the measurement-intervals.
    If you want to measure those as well, you must call `.measure()` again, with
    no `measurement_list` provided.

Indices and tables
==================

* :ref:`search`
