import string
import unittest
from configparser import RawConfigParser
from typing import Any, Callable, List, Union

import hypothesis.strategies as st
from hypothesis import HealthCheck, example, given, settings

import imperfect

whitespace = (" ", "\t", "\n", "\r")
line_noise = ("#", ";", "=", ":")
letters = ("a", "b", "c")
chars = st.characters()


@st.composite
def simple_well_formed_ini(draw: Callable[[Any], str]) -> str:
    section_name = draw(st.text())
    item_name = draw(st.text())
    item_value = draw(st.text())
    template = "x[x{section_name}x]xx{item_name}x=x{item_value}x"
    # replace all the 'x' with a random whitespace
    while True:
        i = template.find("x")
        if i == -1:
            break
        template = template[:i] + draw(st.text(alphabet=" \t\r\n")) + template[i + 1 :]
    return template.format(**locals())


@st.composite
def ini_section(draw: Callable[[Any], str]) -> str:
    section_name = draw(st.text(alphabet=chars))
    template = "x[x{section_name}x]x"
    while True:
        i = template.find("x")
        if i == -1:
            break
        template = (
            template[:i] + draw(st.text(alphabet=string.whitespace)) + template[i + 1 :]
        )
    return template.format(**locals())


@st.composite
def ini_value(draw: Callable[[Any], str]) -> str:
    a = draw(st.text(alphabet=chars))
    b = draw(st.text(alphabet=chars))
    c = draw(st.text(alphabet=chars))
    eq = draw(st.text(alphabet="=:"))
    template = "x{a}x{eq}x{b}x{c}x"
    while True:
        i = template.find("x")
        if i == -1:
            break
        template = (
            template[:i] + draw(st.text(alphabet=string.whitespace)) + template[i + 1 :]
        )
    return template.format(**locals())


@st.composite
def continued_value(draw: Callable[[Any], str]) -> str:
    whitespace = draw(st.text(alphabet=string.whitespace))
    value = draw(st.text())
    return whitespace + value


def configparser_is_ok_with_it(**kwargs: Any) -> Callable[..., bool]:
    def inner(text: Union[List[str], str]) -> bool:
        if isinstance(text, list):
            text = "\n".join(text)

        try:
            RawConfigParser(strict=True, **kwargs).read_string(text)
            return True
        except Exception:
            return False

    return inner


class ImperfectHypothesisTest(unittest.TestCase):
    @given(simple_well_formed_ini().filter(configparser_is_ok_with_it()))
    @example("[a]\nb=1")
    @settings(max_examples=1000, deadline=10)  # type: ignore
    def atest_parse(self, text: str) -> None:
        print("Validating", repr(text))
        rcp = RawConfigParser(strict=True)
        rcp.read_string(text)

        conf = imperfect.parse_string(text)

        for section in rcp:
            if section != "DEFAULT":
                self.assertIn(section, conf)  # type: ignore
                self.assertEqual(
                    conf[section].keys(), list(rcp[section].keys()),
                )

    @given(
        st.lists(ini_section() | ini_value() | continued_value(), min_size=2).filter(
            configparser_is_ok_with_it()
        )
    )
    @settings(  # type: ignore
        suppress_health_check=[HealthCheck.too_slow], max_examples=200, deadline=3000
    )
    @example(["[\r]", " 0=1"])
    @example(["[0]", " 0=", " [ ]"])
    @example(["[ ]", " 0=", " [\r]"])
    @example(["[ ]", "0=", "[  ]", " [0]"])
    @example(["[ ]", "0=", "  []", " ="])
    @example(["[ ]", "0=", "  =", " ="])
    @example(["[ ]", "0=", "[0]", " [\r]"])
    def test_parse(self, lines: List[str]) -> None:
        text = "\n".join(lines)
        rcp = RawConfigParser(strict=True)
        rcp.read_string(text)
        print("Validating", repr(text))
        print("  ", {k: dict(rcp[k]) for k in rcp if k != "DEFAULT"})

        conf = imperfect.parse_string(text)

        for section in rcp:
            if section != "DEFAULT":
                self.assertIn(section, conf)  # type: ignore
                self.assertEqual(
                    conf[section].keys(), list(rcp[section].keys()),
                )

    # @given(
    #     st.lists(ini_section() | ini_value() | continued_value(), min_size=2).filter(
    #         configparser_is_ok_with_it(empty_lines_in_values=False)
    #     )
    # )
    # @settings(
    #     suppress_health_check=[HealthCheck.too_slow], max_examples=200, deadline=3000
    # )
    # @example(['[ ]', '0:', '', ' [0]'])
    # def test_parse_no_empty_lines_in_values(self, lines):
    #     text = "\n".join(lines)
    #     rcp = RawConfigParser(strict=True, empty_lines_in_values=False)
    #     rcp.read_string(text)
    #     print("Validating", repr(text))
    #     print("  ", {k: dict(rcp[k]) for k in rcp if k != "DEFAULT"})

    #     conf = imperfect.parse_string(text, empty_lines_in_values=False)

    #     for section in rcp:
    #         if section != "DEFAULT":
    #             self.assertIn(section, conf)
    #             self.assertEqual(
    #                 conf[section].keys(), list(rcp[section].keys()),
    #             )
