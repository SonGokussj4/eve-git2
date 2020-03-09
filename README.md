# eve-git2

> Updated eve-git utility to ease working with git/gitea

> CUSTOM GITIGNORE\
> root/gitea_data/gitea/options/gitignore/Evektor


## Help
```Bash
usage: eve_git.py [-h] [-v] [-V] <command> ...

Description:
   <Ideally one line description of the program>

optional arguments:
  -h, --help     show this help message and exit
  -v             Verbal (default: None)
  -V, --version  show program's version number and exit

commands:
  clone          Clone one thing!!!
  list           List all the things!!!
  list_org       List all the Orgs!!!
  create         Create one thing!!!
  create_org     Create one org thing!!!
  remove         Remove one thing!!!
  remove_org     Remove one ORG thing!!!
  edit           Edit all the things!!!
  deploy         Deploy all the things!!!

--- Arguments common to all sub-parsers ---
optional arguments:
  -v             Verbal
  -V, --version  show program's version number and exit
```

## Linux Installation & Run

```Bash
python3.7eve -m venv .env
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