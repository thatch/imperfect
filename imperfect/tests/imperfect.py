import configparser
import io
import itertools
import unittest
from typing import List, Optional

from parameterized import parameterized

import imperfect

SAMPLES = [
    "[s]\nb=1",
    "[s]\nb=1\nc=2",
    "[s]\nb=1\n\n",
]

# This is for future adaptation to hypothesis, perhaps
def variations(section: Optional[str], k: str, v: str) -> List[str]:
    assert section
    section_strs = [f"\n\n[{section}]\n", f"[{section}]\n"]
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
    # The goal is to get to 100% test coverage with these, but then also have
    # the hypothesis-based tests that validate behavior on many invented
    # examples.
    @parameterized.expand(  # type: ignore
        [("[s]\na=1",), ("[s]\na = 1",), ("[s]\na = 1\n",), ("[s]\na=\n  1",),],
    )
    def test_simple_parse(self, example: str) -> None:
        conf = imperfect.parse_string(example)
        # Minimal mapping api
        self.assertEqual(["s"], conf.keys())
        self.assertTrue("s" in conf)
        self.assertEqual(["a"], conf["s"].keys())
        self.assertTrue("a" in conf["s"])

        # KeyError coverage
        self.assertFalse("b" in conf)
        self.assertFalse("b" in conf["s"])

        self.assertIn(conf["s"]["a"], ("1", "\n1"))

    @parameterized.expand([("a=1",),],)  # type: ignore
    def test_fail_to_parse(self, example: str) -> None:
        with self.assertRaises(imperfect.ParseError):
            imperfect.parse_string(example)

    def test_multiline_with_comment(self) -> None:
        conf = imperfect.parse_string("[s]\na=\n #comment\n b\n")
        self.assertEqual("\nb", conf["s"]["a"])

    def test_allow_no_value(self) -> None:
        conf = imperfect.parse_string("[s]\na=", allow_no_value=True)
        self.assertEqual("", conf["s"]["a"])

    def test_alternate_delimiters(self) -> None:
        conf = imperfect.parse_string("[s]\naqq1", delimiters=("qq",))
        self.assertEqual("1", conf["s"]["a"])

    def test_alternate_delimiters_allow_no_value(self) -> None:
        conf = imperfect.parse_string(
            "[s]\naqq", delimiters=("qq",), allow_no_value=True
        )
        self.assertEqual("", conf["s"]["a"])

    def test_comment_prefixes(self) -> None:
        conf = imperfect.parse_string("[s]\n@comment\na=1", comment_prefixes=("@",))
        self.assertEqual("1", conf["s"]["a"])

    @parameterized.expand(  # type: ignore
        [
            ("[ ]=",),
            (" [0]",),
            ("[s]\na=1",),
            ("[s]\n[s2]\na=1",),
            ("[s]\n  a = 1  \n\n",),
            ("#comment\n[s]\na=1\n#comment2",),
        ],
        name_func=(lambda a, b, c: f"{a.__name__}_{b}"),
    )
    def test_simple_roundtrips(self, example: str) -> None:
        conf = imperfect.parse_string(example)
        buf = io.StringIO()
        conf.build(buf)
        self.assertEqual(buf.getvalue(), example)

    def test_exhaustive_roundtrip(self) -> None:
        for example in variations("sect", "a", "1"):
            oracle = configparser.RawConfigParser()
            try:
                oracle.read_string(example)
                self.assertEqual(oracle["sect"]["a"], "1")
            except Exception:  # pragma: no cover
                continue

            conf = None
            try:
                conf = imperfect.parse_string(example)
                # Did we parse the same value as configparser
                self.assertEqual(len(conf["sect"].entries), 1)
                self.assertEqual(conf["sect"].entries[0].key, "a")
                self.assertEqual(conf["sect"].entries[0].interpret_value(), "1")
            except Exception:  # pragma: no cover
                print("Input: ", repr(example))
                if conf:
                    # if conf.default:
                    #     print("default:")
                    #     for v in conf.default.entries:
                    #         print("  ", v)
                    for s in conf.sections:
                        print(f"{s.name}:")
                        for v in s.entries:
                            print("  ", v)
                raise

            buf = io.StringIO()
            conf.build(buf)
            self.assertEqual(buf.getvalue(), example)

    def test_example_from_readme(self) -> None:
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

        self.assertEqual(EXPECTED, buf.getvalue())

        temp = "".join(
            difflib.unified_diff(
                data.splitlines(True), buf.getvalue().splitlines(True),
            )
        )
        self.assertTrue(temp)
