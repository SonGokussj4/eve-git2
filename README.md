# eve-git2

> Updated eve-git utility to ease working with git/gitea

> CUSTOM GITIGNORE\
> root/gitea_data/gitea/options/gitignore/Evektor


## Help
```Bash
usage: eve_git.py [-h] [-v] [-V] [--token [TOKEN]] [--bighelp] <command> ...

Description:
   <Ideally one line description of the program>

optional arguments:
  -h, --help       show this help message and exit
  -v               Verbal (default: None)
  -V, --version    show program version number and exit
  --token [TOKEN]  Add or Update your GITEA_TOKEN (default: None)
  --bighelp        Show every possible command (default: False)

commands:
  clone            Clone selected repo into current folder
  list             List {repo/org}. Max 50 items displayed.
  create           Create {repo/org}
  remove           Remove {repo/org}
  edit             Edit remote repo Description
  transfer         Transfer repository to different User/Group
  connect          Connect current repository to remote one
  deploy           Deploy selected repository to production
  template         Choose one of the templates and copy here.
  python           Python {teplate/venv}

--- Arguments common to all sub-parsers ---
optional arguments:
  -v             Verbal
  -V, --version  show program version number and exit

---------- Sub-arguments Details ----------

 clone
   positional arguments:
     repository     Repository name
     username       Specify User/Org (default: None)

 list
   commands:
     repo           List remote Repositories. Max 50 items displayed.
     org            List remote Organizations. (Admin only)

 create
   commands:
     repo           Create Repository (and clone it to current dir)
     org            Create Organization

 remove
   commands:
     repo           Remove Repository
     org            Remove Organization. Has to be empty.

 edit
   positional arguments:
     repository     Help for <repository> (default: None)
     username       Specify User/Org (default: None)

 transfer
   positional arguments:
     repository     Specify Repository for transfer (default: )
     username       Specify User/Org (default: )
     new_owner      Specify target User/Org (default: )

 connect
   positional arguments:
     repository     Specify Repository to connect to (default: )
     remote_name    git remote add <remote_name> (default: gitea)

 deploy
   positional arguments:
     repository     Repository name
     username       Specify User/Org (default: None)
     branch         Branch to deploy (default: master)

 template


 python
   commands:
     template       Managing templates
     venv           Manipulating with environments
```

## Linux Installation & Run

```Bash
python3.7 -m venv .env
.env/bin/pip install update pip
.env/bin/pip install -r requirements.txt

./run.sh
```

## Windows Installation & Run
```Bash
python3.7.exe -m venv .env
.env/Scripts/pip install update pip
.env/Scripts/pip install -r requirements.txt

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
