## v0.3.0

* Add `.index` method used by the mapping methods on both `ConfigFile` and
  `ConfigSection`.  It returns the first match, like lists do, and is
  case-insensitive by default.
* Add item deletion, e.g. `del conf["sectionname"]`
* Update skel, no longer produce `py2.py3` wheels and put `setup_requires` in
  `pyproject.toml`
* Bug fix: Include missing requirements.txt, reference from `make setup`
* Bug fix: when using `set_value` with empty string, don't forget the newline.

## v0.2.0

* Add `ConfigFile.text` property
* Sample code now uses `moreorless`
* Better types on `.build`
* Bug fix: when using `set_value` with multiline strings, don't include a
  trailing whitespace

## v0.1.1

* Bug fix: whem using `set_value` and it adds a section to the end of the file,
  include a blank line before.

## v0.1.0

* When using `set_value` with multiline strings, include hanging indent instead
  of requiring the caller to do so.

## v0.0.3

* Improve CI config
* Include tests and py.typed
* Add `.set_value`

## v0.0.2

* More directly match configparser behavior, coverage to 90%

## v0.0.1

* Initial commit, coverage at 75%
