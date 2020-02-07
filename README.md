# eve-git2

> Updated eve-git utility to ease working with git/gitea

## Help
```
usage: eve-git.py [-h] [--version] [--no-groups] [--no-color] [--img username]
                  [--tel username [username ...]] [--id username [username ...]]
                  [--all] [--write-db]
                  [users [users ...]]

<Ideally one line description of the program>

<
More description
with more lines
or examples
>

positional arguments:
  users                          Optional... <Users> (default: [])

optional arguments:
  -h, --help                     show this help message and exit
  --version                      show program's version number and exit
  --no-groups                    Optional... <Don't show groups> (default: False)
  --no-color                     Optional... <Don't show colors> (default: False)
  --img username                 Optional... <Username (one) to show picture> (default: None)
  --tel username [username ...]  Optional... <Username (one) to show telephone> (default: None)
  --id username [username ...]   Optional... <Username (one) to show user ID number> (default: None)
  --all                          Optional... <Show all people> (default: False)
  --write-db                     Developer only... <Save people into Pickled database> (default: False)
```

## Installation

```
python3.7eve -m venv .env
source .env/bin/activate
pip install update pip
pip install -r requirements
deactivate
```

## Running
```
./run.sh
```
