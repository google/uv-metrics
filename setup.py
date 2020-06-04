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
from setuptools import setup, find_packages

with open('README.md') as f:
  readme = f.read()


def with_versioneer(f, default=None):
  """Attempts to execute the supplied single-arg function by passing it
versioneer if available; else, returns the default.

  """
  try:
    import versioneer
    return f(versioneer)
  except ModuleNotFoundError:
    return default


CASFS_VERSION = "0.1.0"
REQUIRED_PACKAGES = [
    "numpy>=1.18.0", "tqdm>=4.42.1", "fs", "fs-gcsfs",
    "casfs @ git+https://source.developers.google.com/p/blueshift-research/r/casfs@{}#egg=casfs"
    .format(CASFS_VERSION), "sqlalchemy"
]

setup(
    name='uv-metrics',
    version=with_versioneer(lambda v: v.get_version()),
    cmdclass=with_versioneer(lambda v: v.get_cmdclass(), {}),
    description='Shared tooling for Blueshift research.',
    long_description=readme,
    python_requires='>=3.6.0',
    author='Blueshift Team',
    author_email='samritchie@google.com',
    url='https://team.git.corp.google.com/blueshift/uv',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=REQUIRED_PACKAGES,
    extras_require={
        "tf": ["tensorflow"],
        "tf-gpu": ["tensorflow-gpu"],
    },
    include_package_data=True,
)
