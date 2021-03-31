#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os
import re

# Always prefer setuptools over distutils
from setuptools import setup, find_packages


# Get the long description from the relevant file
readme = ''
with open('README.rst', 'r') as f:
    for line in f:
        # raw keyword is unsupported so README.rst
        # below NDEx2 Client Objects header line is being omitted
        if line.startswith('**NDEx2 Client Objects**'):
            break
        readme = readme + line

with open('HISTORY.rst') as history_file:
    history = history_file.read()


with open(os.path.join('ndex2', 'version.py')) as ver_file:
    for line in ver_file:
        if line.startswith('__version__'):
            version=re.sub("'", "", line[line.index("'"):])


test_requirements = [
    'unittest2',
    'requests-mock',
    'nose'
]


if __name__ == '__main__':
    setup(
        name='ndex2',

        # Versions should comply with PEP440.  For a discussion on single-sourcing
        # the version across setup.py and the project code, see
        # https://packaging.python.org/en/latest/single_source_version.html
        version=version,

        description='Nice CX Python includes a client and a data model.',
        long_description=readme + '\n\n' + history,

        # The project's main homepage.
        url='https://github.com/ndexbio/ndex2-client',

        # Author details
        author='The NDEx Project',
        author_email='contact@ndexbio.org',

        # Choose your license
        license='BSD',

        # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers=[
            # How mature is this project? Common values are
            #   3 - Alpha
            #   4 - Beta
            #   5 - Production/Stable
            'Development Status :: 5 - Production/Stable',

            # Indicate who your project is intended for
            'Intended Audience :: Science/Research',
            'Topic :: Scientific/Engineering :: Information Analysis',
            'Topic :: Scientific/Engineering :: Bio-Informatics',
            'Topic :: Scientific/Engineering :: Medical Science Apps.',

            # Pick your license as you wish (should match "license" above)
            'License :: OSI Approved :: BSD License',

            # Specify the Python versions you support here. In particular, ensure
            # that you indicate whether you support Python 2, Python 3 or both.
            'Programming Language :: Python :: 3.6',
        ],

        # What does your project relate to?
        keywords='network analysis biology',

        # You can just specify the packages manually here if your project is
        # simple. Or you can use find_packages().
        packages=find_packages(include=['ndex2', 'ndex2cx']),

        test_suite='tests',
        tests_require=test_requirements,
        install_requires=[
            'six',
            'ijson',
            'requests',
            'requests_toolbelt',
            'networkx',
            'urllib3>=1.16',
            'pandas',
            'enum34; python_version < "3.4"',
            'numpy',
            'enum; python_version == "2.6" or python_version=="2.7"'
        ],

        include_package_data=True
    )
