"""Utility functions used by the SQL reporter and reader.

"""

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from typing import Union


def sqlite_engine(location: str, verbose=False) -> Engine:
  """Currently this just creates a local sqlalchemy engine in a local file.

  """
  if not location.endswith(".db"):
    location = f"{location}.db"

  return create_engine(f'sqlite:///{location}', echo=verbose)


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
