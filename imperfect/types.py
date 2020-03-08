from dataclasses import dataclass, field
from typing import Any, List


class ParseError(Exception):
    pass


@dataclass
class ConfigFile:
    sections: List["ConfigSection"] = field(default_factory=list)
    # The naming of these comes from configobj
    initial_comment: str = ""
    final_comment: str = ""

    def keys(self) -> List[str]:
        return [s.name for s in self.sections]

    def __getitem__(self, name: str) -> "ConfigSection":
        for s in self.sections:
            if s.name == name:
                return s
        raise KeyError(f"Missing section {name}")

    def __contains__(self, name: str) -> bool:
        try:
            self[name]
            return True
        except KeyError:
            return False

    # TODO file-like type
    def build(self, buf: Any) -> None:
        buf.write(self.initial_comment)
        for s in self.sections:
            s.build(buf)
        buf.write(self.final_comment)

    def set_value(self, section: str, key: str, value: str) -> None:
        try:
            s = self[section]
        except KeyError:
            s = ConfigSection(
                leading_square_bracket="[",
                name=section,
                trailing_square_bracket="]",
                newline="\n",
                leading_whitespace="\n" if len(self.sections) else "",
                trailing_whitespace="",
            )
            self.sections.append(s)
        s.set_value(key, value)


@dataclass
class ConfigSection:
    leading_whitespace: str
    leading_square_bracket: str
    name: str
    trailing_square_bracket: str
    trailing_whitespace: str
    newline: str
    entries: List["ConfigEntry"] = field(default_factory=list)

    # TODO file-like type
    def build(self, buf: Any) -> None:
        buf.write(
            self.leading_whitespace
            + self.leading_square_bracket
            + self.name
            + self.trailing_square_bracket
            + self.trailing_whitespace
            + self.newline
        )
        for e in self.entries:
            e.build(buf)

    def keys(self) -> List[str]:
        return [e.key.lower() for e in self.entries]

    def __getitem__(self, name: str) -> str:
        for e in self.entries:
            if e.key.lower() == name.lower():
                return e.interpret_value()
        raise KeyError(name)

    def __contains__(self, name: str) -> bool:
        try:
            self[name]
            return True
        except KeyError:
            return False

    def set_value(self, key: str, value: str) -> None:
        valuelines = [
            ValueLine(
                text=line,
                newline="\n",
                whitespace_before_text="  " if i > 0 else "",
                whitespace_after_text="",
            )
            for i, line in enumerate(value.splitlines(False))
        ]

        for e in self.entries:
            if e.key.lower() == key:
                e.value = valuelines
                break
        else:
            self.entries.append(
                ConfigEntry(
                    key=key,
                    equals="=",
                    value=valuelines,
                    whitespace_before_equals=" ",
                    whitespace_before_value=" ",
                )
            )


@dataclass
class ConfigEntry:
    key: str
    equals: str
    value: List["ValueLine"] = field(default_factory=list)

    whitespace_before_key: str = ""
    whitespace_before_equals: str = ""
    whitespace_before_value: str = ""
    whitespace_after_value: str = ""  # The final (though optional) newline

    def interpret_value(self) -> str:
        return "".join(
            [
                v.text + (v.newline if i < (len(self.value) - 1) else "")
                for i, v in enumerate(self.value)
            ]
        )

    # TODO
    def build(self, buf: Any) -> None:
        buf.write(
            self.whitespace_before_key
            + self.key
            + self.whitespace_before_equals
            + self.equals
            + self.whitespace_before_value
        )
        for v in self.value:
            v.build(buf)
        buf.write(self.whitespace_after_value)


@dataclass
class ValueLine:
    whitespace_before_text: str
    text: str
    whitespace_after_text: str
    newline: str

    # TODO
    def build(self, buf: Any) -> None:
        buf.write(
            self.whitespace_before_text
            + self.text
            + self.whitespace_after_text
            + self.newline
        )
