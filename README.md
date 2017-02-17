# dactyl
Tools to help create Ripple documentation.

How to Install
```
# Optionally create a virtualenv to install the package and all dependencies in
virtualenv -p `which python3` venv_dactyl
# Activate your new python working environment
source venv_dactyl/bin/activate

# Initially check out this repo and then run
pip install dactyl/

# Where 'dactyl/' is the top level directory of the repo, containing setup.py.
# And note the trailing '/' which tells pip to use a local directory to install it.
```

How to Use
```
# Change directory to your documentation project containing a dactyl-config.yml
# and simply run:
dactyl_build -s -t $PROJECT
```
