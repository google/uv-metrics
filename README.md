# UV

UV is Blueshift's shared research codebase. You can find the project's main
documentation and a detailed description of what lives here and how to use it at
<http://go/bs-uv>.

The main thing that lives here now is a series of modules designed to make it
easy to:

- record timeseries measurements during the course of training a neural network
- persist those measurements to a variety of stores
- load those measurements back out for charting and analysis

This page covers the details of how to

- Use the `blueshift-uv` library in your project, both in and out of an isolated
  [Caliban](http://go/caliban) environment
- Develop against `blueshift-uv`, run its tests and contribute code

## Installing UV

The [Installing UV](http://go/bs-uv#installing-uv) section of UV's [g3doc
documentation](http://go/bs-uv#installing-uv) describes at length how to require
the `blueshift-uv` library in your project, in and out of Docker containers.
Head [to those docs](http://go/bs-uv#installing-uv) for the full story.

Here's a short version, since you made it here.

`blueshift-uv` is hosted on [Nest's artifactory
instance](https://artifactory2.nestlabs.com/). This is currently the easiest way
to make `blueshift-uv` accessible inside of Docker containers.

Run this command to install `uv` using `pip`:

```bash
pip install blueshift-uv --extra-index-url https://artifactory2.nestlabs.com/artifactory/api/pypi/pypi-local/simple
```

You can also add the artifactory instance to your permanent list of indexes to
search by adding this line to `~/.pip/pip.conf`:

```yaml
[global]
extra-index-url = https://artifactory2.nestlabs.com/artifactory/api/pypi/pypi-local/simple
```

After this, you can install `blueshift-uv` with the usual `pip` incantations:

```
pip install blueshift-uv
```

### Installing from Git-on-Borg Source

If you want to install the library directly from source, you can use `pip` to
pull from the UV git repository directly:

```bash
pip install -e git+sso://team/blueshift/uv#egg=blueshift-uv
```

Note that this will *not* work inside of a Docker container or
[Caliban](http://go/caliban) build, as the container doesn't have the
credentials required to access `sso://` URLs.

If you're want to install a specific branch, append it to the repo URL like
this:

```bash
pip install -e git+sso://team/blueshift/uv@{{USERNAME}}/my_branch#egg=blueshift-uv
```

## Developing in UV

So you want to add some code to `blueshift-uv`. Excellent!

### Checkout and pre-commit hooks

First, check out the repo:

```
git clone sso://team/blueshift/uv && cd uv
```

Then run this command to install a special pre-commit hook that Gerrit needs to
manage code review properly. You'll only have to run this once.

```bash
f=`git rev-parse --git-dir`/hooks/commit-msg ; mkdir -p $(dirname $f) ; curl -Lo $f https://gerrit-review.googlesource.com/tools/hooks/commit-msg ; chmod +x $f
```

We use [pre-commit](https://pre-commit.com/) to manage a series of git
pre-commit hooks for the project; for example, each time you commit code, the
hooks will make sure that your python is formatted properly. If your code isn't,
the hook will format it, so when you try to commit the second time you'll get
past the hook.

All hooks are defined in `.pre-commit-config.yaml`. To install these hooks,
install `pre-commit` if you don't yet have it. I prefer using [pipx](https://github.com/pipxproject/pipx) so that `pre-commit` stays globally available.

```bash
pipx install pre-commit
```

Then install the hooks with this command:

```bash
pre-commit install
```

Now they'll run on every commit. If you want to run them manually, you can run either of these commands:

```bash
pre-commit run --all-files

# or this, if you've previously run `make build`:
make lint
```

### Aliases

You might find these aliases helpful when developing in UV:

```
[alias]
	review = "!f() { git push origin HEAD:refs/for/${1:-master}; }; f"
	amend  = "!f() { git add . && git commit --amend --no-edit; }; f"
```

### New Feature Workflow

To add a new feature, you'll want to do the following:

- create a new branch off of `master` with `git checkout -b my_branch_name`.
  Don't push this branch yet!
- run `make build` to set up a virtual environment inside the current directory.
- periodically run `make pytest` to check that your modifications pass tests.
- to run a single test file, run the following command:

```bash
env/bin/pytest tests/path/to/your/test.py
```

You can always use `env/bin/python` to start an interpreter with the correct
dependencies for the project.

When you're ready for review,

- commit your code to the branch (multiple commits are fine)
- run `git review` in the terminal. (This is equivalent to running `git push
  origin HEAD:refs/for/master`, but way easier to remember.)

The link to your pull request will show up in the terminal.

If you need to make changes to the pull request, navigate to the review page and
click the "Download" link at the bottom right:

![](https://screenshot.googleplex.com/4BP8v3TWq4R.png)

Copy the "checkout" code, which will look something like this:

```bash
git fetch "sso://team/blueshift/uv" refs/changes/87/670987/2 && git checkout FETCH_HEAD
```

And run that in your terminal. This will get you to a checkout with all of your
code. Make your changes, then run `git amend && git review` to modify the pull
request and push it back up. (Remember, these are aliases we declared above.)

## Publishing UV

`blueshift-uv` is hosted on [Nest's artifactory
instance](https://artifactory2.nestlabs.com/).

The first step to publishing `blueshift-uv` is to follow the instructions at [this
guide](http://go/nest-pypi-local#generating-your-api-key). Once you:

- Log in to [Artifactory](https://artifactory2.nestlabs.com/)
- Generate your API Key
- create `~/.pypirc` as described in the guide

You're ready to publish.

- First, run `make build` to get your virtual environment set up.
- Make sure that you're on the master branch!
- add a new tag, with `git tag 0.2.3` or the equivalent
- `git push; git push --tags`
- run `make release` to package and push `blueshift-uv` to artifactory.

## Trouble?

Get in touch with [samritchie@x.team](mailto:samritchie@x.team).
