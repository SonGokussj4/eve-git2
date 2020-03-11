# eve-git2

> Updated eve-git utility to ease working with git/gitea

> CUSTOM GITIGNORE\
> root/gitea_data/gitea/options/gitignore/Evektor


## Help
```Bash
usage: eve_git.py [-h] [-v] [-V] [--token [TOKEN]] <command> ...

Description:
   <Ideally one line description of the program>

optional arguments:
  -h, --help       show this help message and exit
  -v               Verbal (default: None)
  -V, --version    show program's version number and exit
  --token [TOKEN]  Add or Update your GITEA_TOKEN (default: None)

commands:
  clone            Clone selected repo into current folder
  list             List remote Repositories. Max 50 items displayed.
  list_org         List remote Oranizations. (Admin only)
  create           Create remote Repository (and clone it to current dir)
  create_org       Create remote Organization
  remove           Remove remote Repository
  remove_org       Remove remote Organization. Has to be empty.
  edit             Edit remote repo Description
  connect          Connect current repository to remote one
  deploy           Deploy selected repository to production
  tamplate         Choose one of the templates and copy here.

--- Arguments common to all sub-parsers ---
optional arguments:
  -v             Verbal
  -V, --version  show program's version number and exit
```

## Linux Installation & Run

```Bash
python3.7 -m venv .env
source .env/bin/activate
pip install update pip
pip install -r requirements.txt
deactivate

./run.sh
```

## Windows Installation & Run
```Bash
python3.7.exe -m venv env
env/Scripts/activate
pip install update pip
pip install -r requirements.txt

python.exe eve_git.py
```

## Testing

```Bash
# (In project root folder)
# Simple testing
.env/bin/pytest

# More verbal (individual files)
.env/bin/pytest -v

# Running only those tests which has 'custom' mark
@pytest.mark.custom
def test_fn():
.env/bin/pytest -m custom

```

## Coverage

```Bash
# (In project root folder)
# Simple coverage, results in terminal
.env/bin/pytest --cov-report term --cov=. tests/

# Simple coverage, results in terminal with lines that are not covered
.env/bin/pytest --cov-report term-missing --cov=. tests/

# Coverage, results in html folder: 'htmlcov' accesible through 'index.html'
.env/bin/pytest --cov-report term-missing --cov=. tests/

```
