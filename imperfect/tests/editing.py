import io
import unittest

from .. import parse_string


class EditingTest(unittest.TestCase):
    def test_existing_section_change_entry_preserves_space(self) -> None:
        # Space around the '=' is not changed when you change the value
        conf = parse_string("[a]\n#comment1\nb = 1\n#comment2\n")
        conf.set_value("a", "b", "2")
        buf = io.StringIO()
        conf.build(buf)
        self.assertEqual("[a]\n#comment1\nb = 2\n#comment2\n", buf.getvalue())

    def test_existing_section_change_entry(self) -> None:
        conf = parse_string("[a]\n#comment1\nb=1\n#comment2\n")
        conf.set_value("a", "b", "2")
        buf = io.StringIO()
        conf.build(buf)
        self.assertEqual("[a]\n#comment1\nb=2\n#comment2\n", buf.getvalue())

    def test_existing_section_new_entry(self) -> None:
        conf = parse_string("[a]\nb = 1\n")
        conf.set_value("a", "c", "2")
        buf = io.StringIO()
        conf.build(buf)
        self.assertEqual("[a]\nb = 1\nc = 2\n", buf.getvalue())

    def test_new_section_new_entry(self) -> None:
        conf = parse_string("")
        conf.set_value("a", "b", "1")
        buf = io.StringIO()
        conf.build(buf)
        self.assertEqual("[a]\nb = 1\n", buf.getvalue())

    def test_multiline_value(self) -> None:
        conf = parse_string("")
        conf.set_value("a", "b", "1\n2")
        buf = io.StringIO()
        conf.build(buf)
        self.assertEqual("[a]\nb = 1\n  2\n", buf.getvalue())

    def test_multiline_value_hanging(self) -> None:
        conf = parse_string("")
        conf.set_value("a", "b", "\n1\n2")
        buf = io.StringIO()
        conf.build(buf)
        self.assertEqual("[a]\nb = \n  1\n  2\n", buf.getvalue())
