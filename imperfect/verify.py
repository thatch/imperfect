import configparser
import io
import sys

from imperfect import parse_string


def verify(name: str) -> None:
    with open(name) as f:
        data = f.read()
    conf = parse_string(data)
    buf = io.StringIO()
    conf.build(buf)
    if data != buf.getvalue():
        print(name, "FAIL ROUND TRIP")
        return

    try:
        co = configparser.RawConfigParser()
        co.read_string(data)
    except Exception as e:
        print(name, "FAIL TO READ IN CONFIGPARSER", e)
        return
    compares = 0
    for section_name in co:
        for key in co[section_name]:
            compares += 1
            expected_value = co[section_name][key]
            try:
                if conf[section_name][key] != expected_value:
                    print(name, section_name, key, "FAIL COMPARE")
                    print("configpar:", repr(expected_value))
                    print("imperfect:", repr(conf[section_name][key]))
                    return
            except Exception as e:
                print(name, section_name, key, "FAIL", str(e))
                return

    if compares == 0:
        print(name, "FAIL EMPTY")
        return

    print(name, "OK")


if __name__ == "__main__":  # pragma: no cover
    for f in sys.argv[1:]:
        verify(f)
