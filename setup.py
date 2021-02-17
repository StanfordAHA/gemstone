from setuptools import setup


setup(
    name='gemstone',
    packages=[
        "gemstone",
    ],
    install_requires=[
        "magma-lang>=2.0.7",
        "mantle",
        "fault",
        "ordered_set",
        "hwtypes",
    ],
)
