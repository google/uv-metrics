#!/usr/bin/python
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Reporter implementation that relies on SQLAlchemy.

Uses this as inspiration:
https://source.cloud.google.com/research-3141/tf2-jax-notebooks/+/master:experiment_manager.py

"""

from itertools import groupby
from typing import Any, Dict, Iterable, List, Optional, Union

import uv.reader.base as rb
import uv.sql.util as u
import uv.types as t
from sqlalchemy import JSON, REAL, Column, Integer, String
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from uv.reporter.base import AbstractReporter

Base = declarative_base()


def create_tables(engine: Engine):
  """This triggers table creation for the classes defined at the top. Run this to
  get your local DB ready before you write any metrics.

  """
  Base.metadata.create_all(engine)


class Experiment(Base):
  """Stores general metadata, about the experiment, and provides a key that links
  together all of the metrics.

  You would create one of these when you create a reporter.

  """

  __tablename__ = 'experiment'
  id = Column(Integer, primary_key=True)
  params = Column(JSON)

  def __repr__(self):
    return u.rep_string(self)


class Metric(Base):
  """An individual metric that we'll report to the table."""
  __tablename__ = 'metrics'

  id = Column(Integer, primary_key=True)
  experiment_id = Column(Integer)
  run_id = Column(Integer)
  step = Column(Integer)
  tag = Column(String)
  value = Column(REAL)

  def __repr__(self):
    return u.rep_string(self)


def new_experiment(e: Union[Engine, sessionmaker],
                   config: Dict[str, Any]) -> Experiment:
  """Generates a new experiment."""
  session = u.session_maker(e)()
  exp = Experiment(params=config)
  session.add(exp)
  session.commit()
  return exp


class SQLReporter(AbstractReporter):
  """SQLite-backed reporter. This currently only does the things that you'd
expect a reporter to be able to do; we don't yet support actual experiment
creation, but that's coming.

  """

  def __init__(self, e: Union[Engine, sessionmaker], experiment: Experiment,
               run_id: int):
    self._make_session = u.session_maker(e)
    self._engine = self._make_session.kw["bind"]
    if not u.sqlite_file_exists(self._engine):
      raise Exception(
          f"{self._engine.url} doesn't exist! Create the database before creating a reporter."
      )
    self._experiment = experiment
    self._run_id = run_id

  def _metric(self, step: int, k: str, v: float) -> Metric:
    """Generates an instance of Metric tied to this specific reporter's
    parameters.

    """
    return Metric(experiment_id=self._experiment.id,
                  run_id=self._run_id,
                  step=step,
                  tag=k,
                  value=v)

  def report_all(self, step: int, m: Dict[t.MetricKey, t.Metric]) -> None:
    session = self._make_session()
    session.add_all([self._metric(step, k, v) for k, v in m.items()])
    session.commit()

  def reader(self) -> rb.AbstractReader:
    return SQLReader(self._make_session, self._experiment, self._run_id)


class SQLReader(rb.AbstractReader, rb.IterableReader):
  """AbstractReader implementation backed by a sqlite store.

  """

  def __init__(self,
               e: Union[Engine, sessionmaker],
               experiment: Experiment,
               run_id: int,
               step_key: Optional[str] = None):
    self._make_session = u.session_maker(e)
    self._engine = self._make_session.kw["bind"]
    if not u.sqlite_file_exists(self._engine):
      raise Exception(
          f"{self._engine.url} doesn't exist! Create the database before creating a reader."
      )

    if step_key is None:
      step_key = "step"

    self._experiment = experiment
    self._run_id = run_id

  def keys(self) -> Iterable[t.Metric]:
    """Returns a list of all keys in the DB for this particular experiment and
    run.

    """
    session = self._make_session()
    tags = session.query(Metric.tag.distinct())
    filtered = tags.filter_by(experiment_id=self._experiment.id,
                              run_id=self._run_id)
    for k in filtered:
      yield k[0]

  def read(self, k: t.MetricKey) -> List[t.Metric]:
    session = self._make_session()
    tags = session.query(Metric.step, Metric.value)
    filtered = tags.filter_by(experiment_id=self._experiment.id,
                              run_id=self._run_id,
                              tag=k)
    return [{
        "step": step,
        "value": v
    } for step, v in filtered.order_by(Metric.step)]

  def _values(self, group):
    """Turns the group into the familiar reader interface return value."""
    return [{"step": step, "value": v} for k, step, v in group]

  def read_all(self,
               ks: List[t.MetricKey]) -> Dict[t.MetricKey, List[t.Metric]]:
    session = self._make_session()
    tags = session.query(Metric.tag, Metric.step, Metric.value)
    filtered = tags.filter_by(
        experiment_id=self._experiment.id,
        run_id=self._run_id,
    ).filter(Metric.tag.in_(ks)).order_by(Metric.tag, Metric.step)

    return {
        k: self._values(group) for k, group in groupby(filtered, lambda t: t[0])
    }
