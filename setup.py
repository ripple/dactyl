"""setuptools based setup module"""

from setuptools import setup


LONG_DESC = 'Tools to generate documentation.'

setup(
    name='dactyl',
    version='0.1.0',
    description='Tools to generate documentation.',
    long_description=LONG_DESC,
    url='https://github.com/ripple/dactyl',
    author='Ripple',
    author_email='rome@ripple.com',
    license='GPL',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Utilities',
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
        'jinja2',
        'Markdown',
        'PyYAML',
        'requests',
        'watchdog'
    ]
)

