from setuptools import setup


def get_version(filename: str):
    import ast

    version = None
    with open(filename) as f:
        for line in f:
            if line.startswith("__version__"):
                version = ast.parse(line).body[0].value.s
                break
        else:
            raise ValueError("No version found in %r." % filename)
    if version is None:
        raise ValueError(filename)
    return version


version = get_version(filename="src/dt_protocols/__init__.py")

line = "daffy"
install_requires = [
    f"aido-protocols-{line}",
    "termcolor",
    "zuper-nodes-z6>=6.0.37",
    "zuper-ipce-z6",
    "zuper-commons-z6",
    "zuper-typing-z6",
    "PyYAML",
    "PyGeometry-z6",
    f"duckietown-world-{line}",
    "progressbar",
    f"duckietown-challenges-{line}",
    "matplotlib",
    "numpy",
]

setup(
    name=f"dt-protocols-{line}",
    version=version,
    keywords="",
    package_dir={"": "src"},
    packages=["dt_protocols"],
    install_requires=install_requires,
    entry_points={
        "console_scripts": [],
    },
)
