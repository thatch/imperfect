from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass
class ConfigFile:
    default: Optional["DefaultConfigSection"] = None
    sections: List["ConfigSection"] = field(default_factory=list)
    # The naming of these comes from configobj
    initial_comment: str = ""
    final_comment: str = ""

    def keys(self):
        return [s.name for s in self.sections]

    def __getitem__(self, name):
        for s in self.sections:
            if s.name == name:
                return s
        raise KeyError(f"Missing section {name}")

    def __contains__(self, name):
        try:
            self[name]
            return True
        except KeyError:
            return False

    def build(self, buf) -> None:
        buf.write(self.initial_comment)
        if self.default:
            self.default.build(buf)
        for s in self.sections:
            s.build(buf)
        buf.write(self.final_comment)


@dataclass
class ConfigSection:
    leading_whitespace: str
    leading_square_bracket: str
    name: str
    trailing_square_bracket: str
    trailing_whitespace: str
    newline: str
    entries: List["ConfigEntry"] = field(default_factory=list)

    def build(self, buf) -> None:
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

    def keys(self):
        return [e.key.lower() for e in self.entries]

    def __getitem__(self, name):
        for e in self.entries:
            if e.key.lower() == name.lower():
                return e.interpret_value()
        raise KeyError(name)

    def __contains__(self, name):
        try:
            self[name]
            return True
        except KeyError:
            return False


@dataclass
class DefaultConfigSection:
    # All leading whitespace just belongs to the first entry
    entries: List["ConfigEntry"] = field(default_factory=list)

    def build(self, buf) -> None:
        for e in self.entries:
            e.build(buf)


@dataclass
class ConfigEntry:
    key: str
    equals: str
    value: List["ValueLine"] = field(default_factory=list)

    whitespace_before_key: str = ""
    whitespace_before_equals: str = ""
    whitespace_before_value: str = ""
    whitespace_after_value: str = ""  # The final (though optional) newline

    def interpret_value(self):
        return "".join(
            [
                v.text + (v.newline if i < (len(self.value) - 1) else "")
                for i, v in enumerate(self.value)
            ]
        )

    def build(self, buf) -> None:
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

    def build(self, buf) -> None:
        buf.write(
            self.whitespace_before_text
            + self.text
            + self.whitespace_after_text
            + self.newline
        )


