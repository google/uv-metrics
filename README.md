# UV

UV is Blueshift's shared research codebase. Get excited!

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

## Testing

This is how to configure tests.

https://g3doc.corp.google.com/devtools/kokoro/g3doc/userdocs/general/gob_scm.md?cl=head

## Developing

Run this to get all of the nice language-checking goodies.

```sh
pip install 'python-language-server[all]'
```

## Publishing

We do this via artifactory.

https://artifactory2.nestlabs.com/artifactory/webapp/#/home

using the info at [this guide](http://go/nest-pypi-local#package-maintainers).

## Trouble?

Get in touch with samritchie@google.com.
