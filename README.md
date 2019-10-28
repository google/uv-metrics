# UV

UV is Blueshift's shared research codebase.

# Code Review

To push code,

First run this:

```sh
f=`git rev-parse --git-dir`/hooks/commit-msg ; mkdir -p $(dirname $f) ; curl -Lo $f https://gerrit-review.googlesource.com/tools/hooks/commit-msg ; chmod +x $f
```

- create a branch
- work!
- commit
- `git push origin HEAD:refs/for/master`

More info to file on the process: https://www.gerritcodereview.com/user-review-ui.html

And info from internally on how code revie works: https://g3doc.corp.google.com/company/teams/gerritcodereview/users/intro-codelab.md?cl=head#create-a-change

# Testing

This is how to configure tests.

https://g3doc.corp.google.com/devtools/kokoro/g3doc/userdocs/general/gob_scm.md?cl=head

# Getting Started

What lives here?

- Measurements
- Testing

# Trouble?

Get in touch with samritchie@google.com.
