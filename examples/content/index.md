# Dactyl

Documentation tools for enterprise-quality documentation from Markdown source. Dactyl has advanced features to enable [single-sourcing](https://en.wikipedia.org/wiki/Single_source_publishing) and an extensible syntax for building well-organized, visually attractive docs. It generates output in HTML (natively), and can make PDFs if you have [Prince][] installed.

[Prince]: http://www.princexml.com/

## Installation

Dactyl requires [Python 3](https://python.org/). Install with [pip](https://pip.pypa.io/en/stable/):

```
sudo pip3 install dactyl
```

Or a local install in a virtualenv:

```sh
# Create an activate a virtualenv so the package and dependencies are localized
virtualenv -p `which python3` venv_dactyl
source venv_dactyl/bin/activate
pip3 install dactyl
```
