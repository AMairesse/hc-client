import ez_setup
from setuptools import setup, find_packages

ez_setup.use_setuptools()


setup(
    name='HC-Client',
    version='0.9.0',
    author='Antoine Mairesse',
    author_email='antoine.mairesse@free.fr',
    packages=find_packages(exclude=['ez_setup']),
    url='',
    license='COPYING',
    description='Client for Heat Control',
    long_description=open('README.md').read(),
    requires=['RPi', 'requests', 'json', 'pytz', 'dateutil'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: No Input/Output (Daemon)",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Topic :: Utilities",
    ],
    entry_points={
        'console_scripts': ['hc-client = src.hcclient.py']
    },
    )
