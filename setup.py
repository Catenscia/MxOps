"""
author: Etienne Wallet

Module to install and build the package
"""
import os
from setuptools import setup, find_packages

from xops import __version__

setup_directory = os.path.abspath(os.path.dirname(__file__))

# retrieve the requirements for the package
requirements_path = os.path.join(setup_directory, 'requirements.txt')
with open(requirements_path, encoding='utf-8') as file:
    requirements_content = file.read()
requirements = requirements_content.split('\n')

# retrieve the README
readme_path = os.path.join(setup_directory, 'README.md')
with open(readme_path, encoding='utf-8') as file:
    readme = file.read()


setup(
    name="xops",
    version=__version__,
    packages=find_packages(),
    license='MIT License',
    python_requires='==3.8',
    install_requires=requirements,
    long_description=readme,
    description="Python package to automate MultiversX smart contracts deployment and contract interactions in general",
    author="Catenscia"
)
