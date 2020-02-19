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


REQUIRED_PACKAGES = ["numpy>=1.18.0", "tqdm>=4.42.1", "fs", "fs-gcsfs"]

setup(
    name='blueshift-uv',
    version=with_versioneer(lambda v: v.get_version()),
    cmdclass=with_versioneer(lambda v: v.get_cmdclass(), {}),
    description='Shared tooling for Blueshift research.',
    long_description=readme,
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
