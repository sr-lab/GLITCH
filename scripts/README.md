# Helper Scripts
In this folder we find scripts used for the extraction of data necessary for code smells:
 - Use of obsolete/deprecated commands or functions

### Requirements
The requirements to run these scripts are in the requirements.txt folder. \
To install them run:
```shell
pip install -r requirements.txt
```

### Use of obsolete/deprecated commands or functions
This code smell requires a list of deprecated/obsolete commands and functions, this list can be
generated with `obsolete_commands_scraper.py`, this script scrapes the book
[Unix in a nutshell](https://docstore.mik.ua/orelly/unix3/unixnut/appb_02.htm) which contains a chapter with
deprecated commands.