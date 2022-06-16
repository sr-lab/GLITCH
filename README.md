# GLITCH

![alt text](https://github.com/sr-lab/GLITCH/blob/main/logo.png?raw=true)

GLITCH is a technology-agnostic framework that enables automated detection of IaC smells. GLITCH allows polyglot smell detection by transforming IaC scripts into an intermediate representation, on which different smell detectors can be defined. GLITCH currently supports the detection of nine different security smells [1, 2] and nine design & implementation smells [3] in scripts written in Puppet, Ansible, or Chef.

## Installation

To install run:
```
python3 -m pip install -e .
```

To use the tool for Chef you also need Ruby and its Ripper package installed.

You should also install the package [puppetparser](https://github.com/Nfsaavedra/puppetparser).

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

## Documentation

More information can be found in [GLITCH's documentation](https://github.com/sr-lab/GLITCH/wiki).

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[GPL-3.0](https://choosealicense.com/licenses/gpl-3.0/)

## References

<sub>[1] Rahman, A., Parnin, C., & Williams, L. (2019, May). The seven sins: Security smells in infrastructure as code scripts. In 2019 IEEE/ACM 41st International Conference on Software Engineering (ICSE) (pp. 164-175). IEEE.</sub>

<sub>[2] Rahman, A., Rahman, M. R., Parnin, C., & Williams, L. (2021). Security smells in ansible and chef scripts: A replication study. ACM Transactions on Software Engineering and Methodology (TOSEM), 30(1), 1-31.</sub>

<sub>[3] Schwarz, J., Steffens, A., & Lichter, H. (2018, September). Code smells in infrastructure as code. In 2018 11th International Conference on the Quality of Information and Communications Technology (QUATIC) (pp. 220-228). IEEE.</sub>
