# eve-git2

> Updated eve-git utility to ease working with git/gitea

> CUSTOM GITIGNORE\
> root/gitea_data/gitea/options/gitignore/Evektor


## Help
```Bash
usage: eve_git.py [-h] [--version] [--create [repository [description ...]] |
                  --clone repository [user ...] | --remove repository
                  [user ...]]

Description:
   <Ideally one line description of the program>

optional arguments:
  -h, --help                               show this help message and exit
  --version                                show program's version number and exit
  --create [repository [description ...]]  Create new remote [repository], [description], [user] (default: None)        --clone repository [user ...]            Clone existing <repository> [user] into current directory (default: None)    --remove repository [user ...]           Remove remote <repository> [user] (default: None)
```

## Installation

```R
python3.7eve -m venv .env
source .env/bin/activate
pip install update pip
pip install -r requirements
deactivate
```

## Running
```Bash
./run.sh
```
