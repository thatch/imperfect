"""
An imperfect configparser-compatible CST.

This is not designed for quick access, it's designed for being able to roundtrip
and splice between files.
"""

import configparser
import io
import re
import sys
#from dataclasses import dataclass, field
#from typing import List, Optional, Tuple

from .types import *


LEADING_WHITESPACE = re.compile(
    r"^([ \t\r\x1f\x1e\x1d\x1c\x0c\x0b]*)(.*?)([ \t]*)(\r?\n)?$"
)
# These do not need to handle leading or trailing whitespace, that's handled
# above.
SECTION = re.compile(r"^(\[)([^\]]+)(\])(.*)")
ENTRY = re.compile(r"(.*?)(\s*)([=:])(\s*)(.*)")


def split_prefix(line: str) -> Tuple[str, str, str, str]:
    r"""
    Given '  a  \n' gives ('  ', 'a', '  ', '\n')
    """
    m = LEADING_WHITESPACE.match(line)
    return m.group(1), m.group(2), m.group(3), m.group(4) or ""


LINE_RE = re.compile(r".*?(?:\n|$)", re.DOTALL)
UNDECIDED = object()


class Parser:

    # These regexes and comments come directly from configparser.py which is
    # available under the MIT license at https://github.com/jaraco/configparser
    # They are not yet used by the live parser.
    # [[[
    # Regular expressions for parsing section headers and options
    _SECT_TMPL = r"""
        \[                                 # [
        (?P<header>[^]]+)                  # very permissive!
        \]                                 # ]
        """
    _OPT_TMPL = r"""
        (?P<option>.*?)                    # very permissive!
        \s*(?P<vi>{delim})\s*              # any number of space/tab,
                                           # followed by any of the
                                           # allowed delimiters,
                                           # followed by any space/tab
        (?P<value>.*)$                     # everything up to eol
        """
    _OPT_NV_TMPL = r"""
        (?P<option>.*?)                    # very permissive!
        \s*(?:                             # any number of space/tab,
        (?P<vi>{delim})\s*                 # optionally followed by
                                           # any of the allowed
                                           # delimiters, followed by any
                                           # space/tab
        (?P<value>.*))?$                   # everything up to eol
        """
    # Compiled regular expression for matching sections
    SECTCRE = re.compile(_SECT_TMPL, re.VERBOSE)
    # Compiled regular expression for matching options with typical separators
    OPTCRE = re.compile(_OPT_TMPL.format(delim="=|:"), re.VERBOSE)
    # Compiled regular expression for matching options with optional values
    # delimited using typical separators
    OPTCRE_NV = re.compile(_OPT_NV_TMPL.format(delim="=|:"), re.VERBOSE)
    # Compiled regular expression for matching leading whitespace in a line
    NONSPACECRE = re.compile(r"\S")
    # ]]]

    def __init__(
        self,
        allow_no_value=False,
        delimiters=("=", ":"),
        comment_prefixes=("#", ";"),
        inline_comment_prefixes=None,
        empty_lines_in_values=True,
    ) -> None:
        self._delimeters = tuple(delimiters)
        if delimiters == ("=", ":"):
            self._optcre = self.OPTCRE_NV if allow_no_value else self.OPTCRE
        else:
            d = "|".join(re.escape(d) for d in delimiters)
            if allow_no_value:
                self._optcre = re.compile(self._OPT_NV_TMPL.format(delim=d), re.VERBOSE)
            else:
                self._optcre = re.compile(self._OPT_TMPL.format(delim=d), re.VERBOSE)
        self._comment_prefixes = tuple(comment_prefixes or ())
        self._inline_comment_prefixes = tuple(inline_comment_prefixes or ())
        self._allow_no_value = allow_no_value
        self._empty_lines_in_values = empty_lines_in_values

    def parse_string(self, text) -> ConfigFile:

        # Note that default_section param isn't included; it doesn't have a name in
        # this tree so it doesn't matter.

        root = ConfigFile()
        sect = None
        entry = None
        entry_indent = None

        wsbuf = ""

        # print("top")
        for line in LINE_RE.findall(text):
            parts = split_prefix(line)
            # print(repr(line), parts)

            # print("loop", repr(line), repr(parts), entry_indent)

            if isinstance(entry_indent, int) and len(parts[0]) > entry_indent:
                # print("continuation")
                if self._empty_lines_in_values:
                    if wsbuf and wsbuf.count("\n") == len(wsbuf):
                        # This will need a refactoring when inline comments work.
                        for char in wsbuf:
                            value = ValueLine(
                                whitespace_before_text="",
                                text="",
                                whitespace_after_text="",
                                newline=char,
                            )
                            entry.value.append(value)
                if parts[2].startswith(("#", ";")) and not parts[1]:
                    parts = list(parts)
                    # This is a comment line
                    parts[2] += parts[3]
                    parts[3] = ""
                value = ValueLine(
                    whitespace_before_text=parts[0],
                    text=parts[1],
                    whitespace_after_text=parts[2],
                    newline=parts[3],
                )
                entry.value.append(value)
                wsbuf = ""
                continue
            elif parts[1].startswith(("#", ";")):
                # Not a continuation, we just ignore.
                wsbuf += line
                continue

            wsbuf += parts[0]
            m = SECTION.match(parts[1])
            if m:
                sect = ConfigSection(
                    leading_whitespace=wsbuf,
                    leading_square_bracket=m.group(1),
                    name=m.group(2),
                    trailing_square_bracket=m.group(3),
                    trailing_whitespace=m.group(4) + parts[2],
                    newline=parts[3],
                )
                # print("Add section", sect)
                root.sections.append(sect)
                wsbuf = ""
                entry_indent = None
                continue

            m = ENTRY.match(parts[1])
            if m:
                entry = ConfigEntry(
                    whitespace_before_key=wsbuf,
                    key=m.group(1),
                    whitespace_before_equals=m.group(2),
                    equals=m.group(3),
                    whitespace_before_value=m.group(4),
                    whitespace_after_value="",
                )
                value = ValueLine(
                    whitespace_before_text="",
                    text=m.group(5),
                    whitespace_after_text=parts[2],
                    newline=parts[3],
                )
                entry.value.append(value)
                if sect is None:
                    sect = DefaultConfigSection()
                    root.default = sect
                sect.entries.append(entry)
                entry_indent = len(parts[0])
                wsbuf = ""
                continue

            wsbuf += line

        # TODO: Try to figure out somewhere to put it...
        if wsbuf:
            root.final_comment = wsbuf

        return root


def parse_string(text, **kwargs) -> ConfigFile:
    return Parser(**kwargs).parse_string(text)
