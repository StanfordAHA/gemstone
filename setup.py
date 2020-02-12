from setuptools import setup


setup(
    name='gemstone',
    packages=[
        "gemstone",
        "gemstone.generator",
        "gemstone.common",
    ],
    install_requires=[
        "mantle",
        "fault",
        "ordered_set",
        "hwtypes",
    ],
)
