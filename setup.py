#!/usr/bin/env python3

"""setuptools based setup module"""

from setuptools import setup

long_description = open('README.md', encoding="utf-8").read()

with open("dactyl/version.py", encoding="utf-8") as versionfile:
    exec(versionfile.read())

setup(
    name='dactyl',
    version=__version__,
    description='Tools to generate documentation.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/ripple/dactyl',
    author='Ripple',
    author_email='rome@ripple.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Utilities',
        'Topic :: Documentation',
    ],
    keywords='documentation',
    packages=[
        'dactyl',
    ],
    entry_points={
        'console_scripts': [
            'dactyl_build = dactyl.dactyl_build:dispatch_main',
            'dactyl_link_checker = dactyl.dactyl_link_checker:dispatch_main',
            'dactyl_style_checker = dactyl.dactyl_style_checker:dispatch_main',
        ],
    },
    install_requires=[
        'argparse',
        'beautifulsoup4',
        'jinja2>=2.11',
        'Markdown>=3.0.1',
        'ruamel.yaml',
        'requests',
        'watchdog',
        'textstat',
        'pyspellchecker'
    ],
    package_data={
        '': ["templates/*", "default-config.yml"],
    }
)
