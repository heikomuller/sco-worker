#! /usr/bin/env python

from setuptools import setup

setup(
    name='sco-worker',
    version='0.3.4',
    description='Library to to execute predictive model run requests',
    keywords='neuroscience vision cortex ',
    author='Heiko Mueller',
    author_email='heiko.muller@gmail.com',
    url='https://github.com/heikomuller/sco-worker',
    license='GPLv3',
    packages=['scoworker'],
    package_data={'': ['LICENSE']},
    install_requires=[
        'pika',
        'neuropythy >= "0.2.26"',
        'pimms >= "0.1.8"',
        'scikit-image',
        'sco-datastore >= "0.5.0"',
        'sco-engine',
        'sco-client'
    ]
)
