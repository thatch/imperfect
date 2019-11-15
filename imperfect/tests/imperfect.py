import configparser
import io
import itertools
import unittest
from typing import List, Optional

from parameterized import parameterized

import imperfect

SAMPLES = [
    "[s]\nb=1",
    "[s]\nb=1\n\n",
    "a=1",
    "a=1\n",
]

# This is for future adaptation to hypothesis, perhaps
def variations(section: Optional[str], k: str, v: str) -> List[str]:
    if section:
        section_strs = [f"\n\n[{section}]\n", f"[{section}]\n"]
    else:
        section_strs = [""]
    return [
        "".join(c)
        for c in itertools.product(
            section_strs,
            ["", "\n"],
            ["", " ", "  ", "\t", "    \t     "],
            [k],
            ["", " "],
            ["=", ":"],
            ["", " "],
            [v],
            ["", "\n", "\n\n"],
        )
    ]


class ImperfectTests(unittest.TestCase):
    @parameterized.expand(
        [
            ("a=1",),
            ("[ ]=",),
            (" [0]",),
            ("[s]\na=1",),
            ("[s]\n[s2]\na=1",),
            ("  a = 1  \n\n",),
            ("#comment\n[s]\na=1\n#comment2",),
        ],
        testcase_func_name=(lambda a, b, c: f"{a.__name__}_{b}"),
    )
    def test_simple_roundtrips(self, example):
        conf = imperfect.parse_string(example)
        buf = io.StringIO()
        conf.build(buf)
        self.assertEqual(buf.getvalue(), example)

    def test_exhaustive_roundtrip(self):
        for example in variations("sect", "a", "1"):
            oracle = configparser.RawConfigParser()
            try:
                oracle.read_string(example)
                self.assertEqual(oracle["sect"]["a"], "1")
            except Exception:
                continue

            conf = None
            try:
                conf = imperfect.parse_string(example)
                # Did we parse the same value as configparser
                self.assertEqual(len(conf["sect"].entries), 1)
                self.assertEqual(conf["sect"].entries[0].key, "a")
                self.assertEqual(conf["sect"].entries[0].interpret_value(), "1")
            except imperfect.TrailingWhitespace:
                continue
            except Exception:
                print("Input: ", repr(example))
                if conf:
                    if conf.default:
                        print("default:")
                        for v in conf.default.entries:
                            print("  ", v)
                    for s in conf.sections:
                        print(f"{s.name}:")
                        for v in s.entries:
                            print("  ", v)
                raise

            buf = io.StringIO()
            conf.build(buf)
            self.assertEqual(buf.getvalue(), example)

    def test_example_from_readme(self):
        INPUT = """
[metadata]
# the package name
name = imperfect
# slurp the readme
long_description = file: README.md

[options]
packages = imperfect
"""
        EXPECTED = """
[metadata]
# the package name
name = imperfect
# slurp the readme
long_description = file: README.md
long_description_content_type =  text/markdown

[options]
packages = imperfect
"""
        import io
        import difflib
        import imperfect

        data = INPUT

        conf: imperfect.ConfigFile = imperfect.parse_string(data)
        metadata_section = conf["metadata"]

        # Ignoring some whitespace for now, this looks like
        # long_description_content_type =  text/markdown\n
        # [                   entry                      ]
        # [            key            ][eq][    value    ]

        value = imperfect.ValueLine(
            whitespace_before_text="",
            text="text/markdown",
            whitespace_after_text="",
            newline="\n",
        )
        new_entry = imperfect.ConfigEntry(
            key="long_description_content_type",
            equals="=",
            value=[value],
            whitespace_before_equals=" ",
            whitespace_before_value="  ",
        )
        for i, entry in enumerate(metadata_section.entries):
            if entry.key == "long_description":
                metadata_section.entries.insert(i + 1, new_entry)
                break

        buf = io.StringIO()
        conf.build(buf)

        print(
            "".join(
                difflib.unified_diff(
                    data.splitlines(True), buf.getvalue().splitlines(True),
                )
            )
        )
        self.assertEqual(EXPECTED, buf.getvalue())
