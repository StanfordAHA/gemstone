from setuptools import setup


setup(
    name='gemstone',
    packages=[
        "gemstone",
        "gemstone.generator",
        "gemstone.common",
    ],
    install_requires=[
        "magma-lang",
        "mantle",
        "fault",
        "ordered_set",
        "hwtypes",
    ],
)
