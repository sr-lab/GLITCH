# GLITCH

GLITCH, a new technology-agnostic framework that enables automated detection of IaC security smells. GLITCH allows polyglot smell detection by transforming IaC scripts into an intermediate representation, on which different security smell detectors can be defined. GLITCH currently supports the detection of nine different security smells in scripts written in Puppet, Ansible, or Chef.

## Installation

To install run:
```
python3 -m pip install -e .

```

## Usage

You can use the command to see all options:
```
python3 -m glitch --help
```

To analyze a file or folder and get the csv results you can run:
```
python3 -m glitch --tech (chef|puppet|ansible) --csv --config PATH_TO_CONFIG PATH_TO_FILE_OR_FOLDER
```

If you want to consider the module structure you can add the flag ```--module```.

## Configs

New configs can be created with the same structure as the ones found in the folder ```configs```.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[GPL-3.0](https://choosealicense.com/licenses/gpl-3.0/)
