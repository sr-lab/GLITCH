# GLITCH

GLITCH is a technology-agnostic framework that enables automated detection of IaC smells. GLITCH allows polyglot smell detection by transforming IaC scripts into an intermediate representation, on which different smell detectors can be defined. The extension allows Infrastructure as Code developers to receive visual feedback for the smells identified in their code, while programming in Visual Studio Code.

## Features

The extension runs GLITCH in the background and provides visual feedback for the detected smells:

![](https://raw.githubusercontent.com/sr-lab/GLITCH/main/vscode-extension/glitch/images/feature.png)

## Requirements

You should install GLITCH before you use this extension. To install GLITCH follow the instructions [here](https://github.com/sr-lab/GLITCH).

## Extension Settings

This extension contributes the following settings:

* `glitch.enable`: Enables/disables the extension.
* `glitch.configurationPath`: Defines the path of the configuration INI file to be used by GLITCH (--config option).
* `glitch.tech`: Defines the technology GLITCH will be considering (--tech option).
* `glitch.smells`: Defines a list of types of smells to be considered by GLITCH (--smells option).

You should define the settings above in the Workspace scope if you want different settings between multiple projects.

## Release Notes

### 0.0.1

First release of the GLITCH extension

### 0.0.2

Fix bug with autodetection option that was removed from GLITCH.