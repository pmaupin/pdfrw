#!/usr/bin/env python

from distutils.core import setup

setup(
    name='pdfrw',
    version='0.2b1',
    description='PDF file reader/writer library',
    long_description='''
pdfrw lets you read and write PDF files, including
compositing multiple pages together (e.g. to do watermarking,
or to copy an image or diagram from one PDF to another),
and can output by itself, or in conjunction with reportlab.

pdfrw will faithfully reproduce vector formats without
rasterization, so the rst2pdf package has used pdfrw
by default for PDF and SVG images by default since
March 2010.  Several small examples are provided.
''',
    author='Patrick Maupin',
    author_email='pmaupin@gmail.com',
    platforms='Independent',
    url='https://github.com/pmaupin/pdfrw',
    packages=['pdfrw', 'pdfrw.objects'],
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
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

        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Software Development :: Libraries',
        'Topic :: Text Processing',
        'Topic :: Utilities',
    ],
    keywords='pdf vector graphics PDF nup watermark',
)
