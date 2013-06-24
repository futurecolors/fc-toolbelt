# coding: utf-8
from setuptools import setup
import fc_toolbelt


setup(
    name='fc-toolbelt',
    version=fc_toolbelt.__VERSION__,
    packages=['fc_toolbelt'],
    install_requires=[
        'fabric>=1.5',
        'fabric-taskset==0.2.1',
        'docopt>=0.6.1',
        'hammock==0.2.4'
    ],
    entry_points={
        'console_scripts': [
            'fct = fc_toolbelt.cli:main',
        ],
    },
    url='https://github.com/futurecolors/fc-toolbelt',
    license='MIT',
    author='Future Colors',
    author_email='info@futurecolors.ru',
    description='A set of useful fabric scripts for everyday use.'
)
