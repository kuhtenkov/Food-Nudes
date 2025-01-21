from setuptools import setup, find_packages

setup(
    name="test_bot",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)