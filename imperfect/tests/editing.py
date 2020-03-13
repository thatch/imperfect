import unittest

from .. import parse_string


class EditingTest(unittest.TestCase):
    def test_existing_section_change_entry_preserves_space(self) -> None:
        # Space around the '=' is not changed when you change the value
        conf = parse_string("[a]\n#comment1\nb = 1\n#comment2\n")
        conf.set_value("a", "b", "2")
        self.assertEqual("[a]\n#comment1\nb = 2\n#comment2\n", conf.text)

    def test_existing_section_change_entry(self) -> None:
        conf = parse_string("[a]\n#comment1\nb=1\n#comment2\n")
        conf.set_value("a", "b", "2")
        self.assertEqual("[a]\n#comment1\nb=2\n#comment2\n", conf.text)

    def test_existing_section_new_entry(self) -> None:
        conf = parse_string("[a]\nb = 1\n")
        conf.set_value("a", "c", "2")
        self.assertEqual("[a]\nb = 1\nc = 2\n", conf.text)

    def test_new_section_new_entry(self) -> None:
        conf = parse_string("")
        conf.set_value("a", "b", "1")
        self.assertEqual("[a]\nb = 1\n", conf.text)

    def test_empty_value(self) -> None:
        conf = parse_string("")
        conf.set_value("a", "b", "")
        self.assertEqual("[a]\nb =\n", conf.text)

    def test_multiline_value(self) -> None:
        conf = parse_string("")
        conf.set_value("a", "b", "1\n2")
        self.assertEqual("[a]\nb = 1\n  2\n", conf.text)

    def test_multiline_value_hanging(self) -> None:
        conf = parse_string("")
        conf.set_value("a", "b", "\n1\n2")
        self.assertEqual("[a]\nb =\n  1\n  2\n", conf.text)

    def test_multiline_value_hanging_edit(self) -> None:
        conf = parse_string("")
        conf.set_value("a", "b", "x")
        conf.set_value("a", "c", "y")
        self.assertEqual("[a]\nb = x\nc = y\n", conf.text)
        conf.set_value("a", "b", "\n1\n2")
        self.assertEqual("[a]\nb =\n  1\n  2\nc = y\n", conf.text)

    def test_set_to_empty_string(self) -> None:
        conf = parse_string("")
        conf.set_value("a", "b", "")
        self.assertEqual("[a]\nb =\n", conf.text)

    def test_set_to_empty_string_edit(self) -> None:
        conf = parse_string("")
        conf.set_value("a", "b", "x")
        conf.set_value("a", "c", "y")
        self.assertEqual("[a]\nb = x\nc = y\n", conf.text)
        conf.set_value("a", "b", "")
        self.assertEqual("[a]\nb =\nc = y\n", conf.text)
        conf.set_value("a", "b", "2")
        self.assertEqual("[a]\nb = 2\nc = y\n", conf.text)

    def test_del_section(self) -> None:
        conf = parse_string("[a]\na=1\n[b]\nb=2\n")
        del conf["a"]
        self.assertEqual("[b]\nb=2\n", conf.text)
        with self.assertRaises(KeyError):
            del conf["c"]

    def test_del_value(self) -> None:
        conf = parse_string("[a]\na=1\naa=2\n[b]\nb=2\n")
        del conf["a"]["aa"]
        self.assertEqual("[a]\na=1\n[b]\nb=2\n", conf.text)
        with self.assertRaises(KeyError):
            del conf["a"]["z"]
