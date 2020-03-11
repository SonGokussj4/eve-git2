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
  clone (cl)       Clone selected repo into current folder
  list (l)         List remote Repositories. Max 50 items displayed.
  list_org (lo)    List remote Oranizations. (Admin only)
  create (c)       Create remote Repository (and clone it to current dir)
  create_org (co)  Create remote Organization
  remove (r)       Remove remote Repository
  remove_org (ro)  Remove remote Organization. Has to be empty.
  edit (e)         Edit remote repo Description
  connect (cn)     Connect current repository to remote one
  deploy (d)       Deploy selected repository to production

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