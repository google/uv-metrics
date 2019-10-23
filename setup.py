from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

REQUIRED_PACKAGES = []
setup(
  name='uv',
  version='0.1.0',
  description='Shared tooling for Blueshift research',
  long_description=readme,
  author='Blueshift Team',
  author_email='samritchie@google.com',
  url='https://team.git.corp.google.com/blueshift/uv',
  packages=find_packages(exclude=('tests', 'docs')),
  install_requires=REQUIRED_PACKAGES,
  include_package_data=True,
)
