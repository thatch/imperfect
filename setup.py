from setuptools import setup


def parse_version():
    with open("imperfect/__version__.py") as f:
        data = f.read()
    d = {}
    exec(data, d)
    return d["__version__"]


setup(
    version=parse_version(),
    python_requires=">=3.6",
    install_requires=[
        "dataclasses >= 0.7; python_version < '3.7'",
    ],
)
