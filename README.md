# GLITCH

[![DOI](https://zenodo.org/badge/453066827.svg)](https://zenodo.org/badge/latestdoi/453066827)
[![License: GPL-3.0](https://badgen.net/github/license/sr-lab/GLITCH)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue)](https://www.python.org/downloads/)
[![Last release](https://badgen.net/github/release/sr-lab/GLITCH/)](https://github.com/sr-lab/GLITCH/releases)

![alt text](https://github.com/sr-lab/GLITCH/blob/main/logo.png?raw=true)

GLITCH is a technology-agnostic framework that enables automated detection of IaC smells. GLITCH allows polyglot smell detection by transforming IaC scripts into an intermediate representation, on which different smell detectors can be defined. GLITCH currently supports the detection of nine different security smells [1, 2] and nine design & implementation smells [3] in scripts written in Puppet, Ansible, or Chef.



## Paper and Academic Usage
"[GLITCH: Automated Polyglot Security Smell Detection in Infrastructure as Code](https://arxiv.org/abs/2205.14371)" is the main paper that describes the implementation of security smells in GLITCH. It also presents a large-scale empirical study  that analyzes security smells on three large datasets containing 196,755 IaC scripts and 12,281,251 LOC.

If you use GLITCH or any of its datasets, please cite:

 - Nuno Saavedra and João F. Ferreira. 2022. [GLITCH: Automated Polyglot Security Smell Detection in Infrastructure as Code](https://arxiv.org/abs/2205.14371). In 37th IEEE/ACM International Conference on Automated Software Engineering (ASE ’22), October 10–14, 2022, Rochester, MI, USA. ACM, New York NY, USA, 12 pages. https://doi.org/10.1145/3551349.3556945  
 

 ```
 @inproceedings{saavedraferreira22glitch,
  title={{GLITCH}: Automated Polyglot Security Smell Detection in Infrastructure as Code},
  author={Saavedra, Nuno and Ferreira, Jo{\~a}o F},
  booktitle={Proceedings of the 37th IEEE/ACM International Conference on Automated Software Engineering},
  year={2022}
}
 ```

## Installation

To install run:
```
python -m pip install -e .
```

To use the tool for Chef you also need Ruby and its Ripper package installed.

## Usage

You can use the command to see all options:
```
glitch --help
```

To analyze a file or folder and get the csv results you can run:
```
glitch --tech (chef|puppet|ansible) --csv --config PATH_TO_CONFIG PATH_TO_FILE_OR_FOLDER
```

If you want to consider the module structure you can add the flag ```--module```.

## Tests

To run the tests for GLITCH go to the folder ```glitch``` and run:
```
python -m unittest discover tests
```

## Configs

New configs can be created with the same structure as the ones found in the folder ```configs```.

## Documentation

More information can be found in [GLITCH's documentation](https://github.com/sr-lab/GLITCH/wiki).

## VSCode extension

GLITCH has a Visual Studio Code extension which is available [here](https://github.com/sr-lab/GLITCH/tree/main/vscode-extension/glitch).

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[GPL-3.0](https://choosealicense.com/licenses/gpl-3.0/)

## References

<sub>[1] Rahman, A., Parnin, C., & Williams, L. (2019, May). The seven sins: Security smells in infrastructure as code scripts. In 2019 IEEE/ACM 41st International Conference on Software Engineering (ICSE) (pp. 164-175). IEEE.</sub>

<sub>[2] Rahman, A., Rahman, M. R., Parnin, C., & Williams, L. (2021). Security smells in ansible and chef scripts: A replication study. ACM Transactions on Software Engineering and Methodology (TOSEM), 30(1), 1-31.</sub>

<sub>[3] Schwarz, J., Steffens, A., & Lichter, H. (2018, September). Code smells in infrastructure as code. In 2018 11th International Conference on the Quality of Information and Communications Technology (QUATIC) (pp. 220-228). IEEE.</sub>
