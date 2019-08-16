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
        "magma-lang==1.0.13",
        "mantle==1.0.6",
        "fault",
        "ordered_set",
        "hwtypes==1.0.13",
    ],
)
