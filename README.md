# imperfect

This is a module for making automated edits to an existing
configparser-compatible ini file.  It operates like a CST, parsing into a tree
of nodes which can then be edited and written back, preserving whitespace and
comments.

# Quick Start

(Tested as `test_example_from_readme` in the test suite)

Let's say you have the following in `setup.cfg`:

```ini
[metadata]
# the package name
name = imperfect
# slurp the readme
long_description = file: README.md

[options]
packages = imperfect
```

and you'd like to make an edit setting `long_description_content_type` in
`[metadata]` but don't care where it goes.  Default is at the end of the section.

```py
import imperfect
import io
with open("setup.cfg") as f:
    data = f.read()

conf: imperfect.ConfigFile = imperfect.parse_string(data)
conf.set_value("metadata", "long_description_content_type", "text/markdown")

print(conf.text)
```

What if you want to have control over the odering, and want it right before
`long_description`?  Now with diffing and more internals...

```py
import moreorless
import imperfect
import io
with open("setup.cfg") as f:
    data = f.read()

conf: imperfect.ConfigFile = imperfect.parse_string(data)
metadata_section = conf["metadata"]

# Ignoring some whitespace for now, this looks like
# long_description_content_type =  text/markdown\n
# [                   entry                      ]
# [            key            ][eq][    value    ]

value = imperfect.ValueLine(
    whitespace_before_text='',
    text='text/markdown',
    whitespace_after_text='',
    newline='\n',
)
new_entry = imperfect.ConfigEntry(
    key="long_description_content_type",
    whitespace_before_equals=" ",
    equals="=",
    whitespace_before_value="  ",
    value = [value],
)
try:
    pos = metadata_section.index("long_description")
except KeyError:
    pos = len(metadata_section.entries)

metadata_section.entries.insert(pos, new_entry)

print(moreorless.unified_diff(data, conf.text, "config.cfg"), end="")
with open("setup.cfg", "w") as f:
    f.write(conf.text)
# or
with open("setup.cfg", "w") as f:
    conf.build(f)
```


# A note on whitespace

Following the convention used by configobj, whitespace generally is accumulated
and stored on the node that follows it.  This does reasonably well for adding
entries, but can have unexpected consequences when removing them.  For example,

```ini
[section1]
# this belongs to k1
k1 = foo
# this belongs to k2
k2 = foo
# k3 = foo (actually belongs to the following section)

[section2]
```

An insertion to the end of `section1` would go between k2 and the k3 comment.
Removing `section2` would also remove the commented-out `k3`.

I'm open to ideas that improve this.


# A note on formats

The goal is to be as compatible as possible with `RawConfigParser`, which
includes keeping some odd behaviors that are bugs that have been around for a
decade and probably can't be changed now.

1. Section names are very lenient.  `[[x]]yy` is a legal section line, and the
   resulting section name is `[x`.  The `yy` here is always allowed (we keep it
   in the tree though), even with `inline_comments` off.
2. `\r` (carriage return) is considered a whitespace, but not a line terminator.
   This is a difference in behavior between `str.splitlines(True)` and
   `list(io)` -- configparser uses the latter.
3. `\t` counts as single whitespace.


# Supported parse options

```
Option                 Default  Imperfect supports
allow_no_value         False    only False
delimiters             =,:      only =,:
comment_prefixes       #,;      only #,;
empty_lines_in_values  True     True (False is very close to working)
```


# Testing

We use hypothesis to generate plausible ini files and for all the ones that
RawConfigParser can accept, we test that we accept, have the same keys/values,
and can roundtrip it.

This currently happens in text mode only.

If you would like to test support on your file, try `python -m imperfect.verify <filename>`


# Why not...

* `configobj` has a completely different method for line continuations
* I'm not aware of others with the goal of preserving whitespace

# Version Compat

Usage of this library should work back to 3.7, but development (and mypy
compatibility) only on 3.10-3.12.  Linting requires 3.12 for full fidelity.

# Versioning

This library follows [meanver](https://meanver.org/) which basically means
[semver](https://semver.org/) along with a promise to rename when the major
version changes.

# License

imperfect is copyright [Tim Hatch](http://timhatch.com/), and licensed under
the MIT license.  See the `LICENSE` file for details.
