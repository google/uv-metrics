Metric Callback
===================

While reporters in `uv-metrics` handle values that have already been measured,
the `MetricCallback` feature allows you to schedule certain measurements to
run at specified intervals (which may be different for each measurement). Each
time the object is called to measure, it returns a dictionary containing
measurements which may be directly passed to a reporter.

A `MetricCallback` object relies on a state dictionary, which contains
everything which could possibly be needed to perform a given measurement. For
example, one part of this state could be the test dataset, another could be
the network parameters.  Note that this state can have static components, like
the test set, which never changes, and dynamic components, like the network
parameters, which change from step to step.  The way these two types of state
are handled is: initially, the `MetricCallback` object is initialized with a
dictionary representing the static components of the state.  At each step, or
whenever the `measure()` method is called, it is called with both the step
number and a dictionary holding the dynamic state.  Internally, these dicts
are merged before being passed to the functions which perform the measurements.

.. code-block:: python

    import uv.manager as m
    import uv.reporter as r

    # make reporter
    reporter = r.MemoryReporter().stepped()

    # make static state dictionary
    static_state = {'test_set': test_dset}

    # initialize manager
    oscilloscope = m.MetricCallback(static_state)

Once the `MetricCallback` is initialized, you must then tell it which
measurements to make (i.e. the meausurement name), when to make the measurement
(i.e. a function of the current step value which outputs `True` when the
msmt is required), and how to make the measurement (i.e. a function of the
full state dictionary).  The measurement is
specified by a dictionary with keys `name`, `trigger`, and `function`.  Here
`name` is a string specifying the measurement name; the `trigger` is a function
of the current step number that outputs `True` when the measurement is required;
and the `function` is a function which can perform a measurement given a state
dictionary.  For example:

.. code-block:: python

    oscilloscope.add_measurement({'name': 'l2_norm',
                                  'trigger': lambda step: step % 10 == 0,
                                  'function': lambda state: l2norm(state['params']}))

Then, during training, we can call the `measure` function, but we need to pass
the objects needed for measurements which vary during traning, e.g.

.. code-block:: python

    for step in training_steps:
        optimizer_state = do_train_step()

        current_dict = {'params': optimizer_state.params}
        step_msmts = oscilloscope.measure(step, current_dict)
        if step_msmts is not None:
            reporter.report_all(step_msmts)

If we want to perform a measurement at any time (say outside the normal
schedule), we can use the same `measure` method, but now we must provide the
argument `measurement_list` as follows:

.. code-block:: python

    msmt = oscilloscope.measure(step, current_dict,
                        measurement_list=['test_acc'])

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
