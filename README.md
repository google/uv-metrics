# UV

UV is Blueshift's shared research codebase. Get excited!

- TODO link to the docs at <http://go/bs-uv>.

## Installing UV

We don't currently have any pinned versions of UV; to use the library, simply
install off of master.

```bash
pip install -e git+sso://team/blueshift/uv#egg=uv
```

If you're developing and want to install a specific branch, append it to the
repo URL:

```bash
pip install -e git+sso://team/blueshift/uv@sritchie/add_notes#egg=uv
```

This works too, using artifactory:

```bash
pip install uv --extra-index-url https://artifactory2.nestlabs.com/artifactory/api/pypi/pypi-local/simple
```

OR, you can add this to `~/.pip/pip.conf`:

```yaml
[global]
extra-index-url = https://artifactory2.nestlabs.com/artifactory/api/pypi/pypi-local/simple
```

And then this will work:

```
pip install uv
```

## Installing Inside Docker

```
pip install blueshift-uv --extra-index-url https://artifactory2.nestlabs.com/artifactory/api/pypi/pypi-local/simple
```

Or do it with a requirements.txt file:

```
--extra-index-url https://artifactory2.nestlabs.com/artifactory/api/pypi/pypi-local/simple
blueshift-uv
```

OR, you can do it in setup.py:

```
'blueshift-uv @ https://artifactory2.nestlabs.com/artifactory/api/pypi/pypi-local/blueshift-uv/0.2.1/blueshift-uv-0.2.1.tar.gz'
```

TODO check if `blueshift-uv[live]` works, for example.

Final option is to

```
# add
git submodule add sso://team/blueshift/uv

# to keep it up to date:
git submodule update --remote
```

Then you can do `pip install -e uv`, or add to the requirements file.

Note that `pip install -e uv[tf]` works too, if you want some submodule.

# Getting Started

What lives here?

-   Measurements
-   Testing

## Code Review

To push code,

First run this:

```sh
f=`git rev-parse --git-dir`/hooks/commit-msg ; mkdir -p $(dirname $f) ; curl -Lo $f https://gerrit-review.googlesource.com/tools/hooks/commit-msg ; chmod +x $f
```

-   create a branch
-   work!
-   commit
-   `git push origin HEAD:refs/for/master`

More info to file on the process:
https://www.gerritcodereview.com/user-review-ui.html

And info from internally on how code review works:
https://g3doc.corp.google.com/company/teams/gerritcodereview/users/intro-codelab.md?cl=head#create-a-change


## Developing

Run this to get all of the nice language-checking goodies.

```sh
pip install 'python-language-server[all]'
```

## Testing

```
make build
make pytest
```

## Publishing

We do this via artifactory.

https://artifactory2.nestlabs.com/artifactory/webapp/#/home

using the info at [this guide](http://go/nest-pypi-local#package-maintainers).

The key is to call `make release`.

## Trouble?

Get in touch with samritchie@google.com.
