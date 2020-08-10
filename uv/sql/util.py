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
"""Utility functions used by the SQL reporter and reader.

"""

import os
from typing import Union

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker


def sqlite_engine(location: str, verbose=False) -> Engine:
  """Currently this just creates a local sqlalchemy engine in a local file.

  """
  if not location.endswith(".db"):
    location = f"{location}.db"

  return create_engine(f'sqlite:///{location}', echo=verbose)


def session_maker(e: Union[Engine, sessionmaker]) -> sessionmaker:
  """Returns a session maker from the specified Engine, or acts as identity if e
  is already a sessionmaker.

  """
  if isinstance(e, sessionmaker):
    return e

  return sessionmaker(bind=e)


def sqlite_file_exists(arg: Union[Engine, URL]) -> bool:
  """Taken from sqlalchemy-utils. We can import that library once we move to
  potentially many databases, since it seems useful to NOT re-implement the
  world once we release this thing, and folks can make their own DBs.

  https://sqlalchemy-utils.readthedocs.io/en/latest/_modules/sqlalchemy_utils/functions/database.html#database_exists

  """
  if isinstance(arg, Engine):
    return sqlite_file_exists(arg.url)

  database = arg.database

  if not os.path.isfile(database) or os.path.getsize(database) < 100:
    return False

  with open(database, 'rb') as f:
    header = f.read(100)

    return header[:16] == b'SQLite format 3\x00'


def rep_string(instance):
  """Returns a pretty string representation for sqlalchemy classes."""
  klass = instance.__class__
  klassname = klass.__name__
  ret = []
  for k in sorted(klass.__dict__.keys()):
    if k[0] != '_':
      ret.append("{}='{}'".format(k, getattr(instance, k)))

  args = ", ".join(ret)
  return "<{}({})>".format(klassname, args)
