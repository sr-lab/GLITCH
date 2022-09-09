from setuptools import find_packages, setup

setup(
    name='glitch',
    version='0.1.0',
    author='Nuno Saavedra',
    author_email='nuno.saavedra@tecnico.ulisboa.pt',
    packages=find_packages(include=['glitch', 'glitch.*']),
    package_data={'glitch.parsers': ['resources/comments.rb.template'],
        '': ['configs/default.ini']},
    description='A tool to analyze IaC scripts',
    install_requires=[
        "ruamel.yaml",
        "ply",
        "click",
        "alive-progress",
        "prettytable",
        "pandas",
        "configparser",
        "pytest",
        "puppetparser",
        "jinja2"
    ],
    entry_points={
        "console_scripts": [
            "glitch = glitch.__main__:main",
        ]
    }
)
