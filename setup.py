# -*- coding: utf-8 -*-
import ast
import os
import re

from setuptools import find_packages, setup

# parse version from API_Load_Test/__init__.py
# _version_re = re.compile(r'__version__\s+=\s+(.*)')
# _init_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "API_Load_Test", "__init__.py")
# with open(_init_file, 'rb') as f:
#     version = str(ast.literal_eval(_version_re.search(
#         f.read().decode('utf-8')).group(1)))

setup(
    name='locustio',
    version=0.0,
    description="Website load testing framework",
    long_description="""Locust is a python utility for doing easy, distributed load testing of a web site""",
    classifiers=[
        "Topic :: Software Development :: Testing :: Traffic Generation",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
    ],
    keywords='',
    author='Jonatan Heyman, Carl Bystrom, Joakim Hamrén, Hugo Heyman',
    author_email='',
    url='https://API_Load_Test.io/',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "gevent>=1.2.2", 
        "flask>=0.10.1", 
        "requests>=2.9.1", 
        "msgpack-python>=0.4.2", 
        "six>=1.10.0", 
        "pyzmq>=16.0.2", 
        "geventhttpclient-wheels",
        'pandas>=0.23.3',
        "PyYAML>=3.13",
        "psycopg2<=2.7.5",
        "psutil>=5.4.6"
    ],
    test_suite="API_Load_Test.test",
    tests_require=['mock'],
    entry_points={
        'console_scripts': [
            'API_Load_Test = API_Load_Test.main:main',
        ]
    },
)
