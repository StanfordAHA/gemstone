from setuptools import setup


setup(
    name='gemstone',
    packages=[
        "gemstone",
        "gemstone.generator",
        "gemstone.common",
    ],
    install_requires=[
        "coreir==2.0.19",
        "magma-lang",
        "mantle",
        "fault",
        "ordered_set",
        "hwtypes",
    ],
)
