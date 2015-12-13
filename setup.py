#!/usr/bin/env python

from setuptools import setup
from pdfrw import __version__ as version
from pdfrw.py23_diffs import convert_load

setup(
    name='pdfrw',
    version=version,
    description='PDF file reader/writer library',
    long_description=convert_load(open("README.rst", 'rb').read()),
    author='Patrick Maupin',
    author_email='pmaupin@gmail.com',
    platforms='Independent',
    url='https://github.com/pmaupin/pdfrw',
    packages=['pdfrw', 'pdfrw.objects'],
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Software Development :: Libraries',
        'Topic :: Text Processing',
        'Topic :: Printing',
        'Topic :: Utilities',
    ],
    keywords='pdf vector graphics PDF nup watermark split join merge',
)
