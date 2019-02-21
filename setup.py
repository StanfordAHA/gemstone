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
        "mantle>=0.1.13",
        "fault>=1.0.7",
        "ordered_set",
    ],
)
