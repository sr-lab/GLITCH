import click, os
from glitch.analysis.rules import RuleVisitor
from glitch.helpers import RulesListOption
from glitch.tech import Tech
from glitch.parsers.cmof import AnsibleParser, ChefParser, PuppetParser
from pkg_resources import resource_filename
from pathlib import Path

# NOTE: These are necessary in order for python to load the visitors.
# Otherwise, python will not consider these types of rules.
from glitch.analysis.design import DesignVisitor 
from glitch.analysis.security import SecurityVisitor

@click.command(help="PATH is the file or folder to analyze.")
@click.option('--tech',
        type=click.Choice(Tech), required=True,
        help="The IaC technology in which the scripts analyzed are written in.")
@click.option('--type',
    type=click.Choice(['script', 'tasks', 'vars'], case_sensitive=False), default='script',
    help="The type of scripts being analyzed. Currently this choice only makes a difference for Ansible.")
@click.option('--config', type=click.Path(), default="configs/default.ini",
    help="The path for a config file. Otherwise the default config will be used.")
@click.option('--module', is_flag=True, default=False,
    help="Use this flag if the folder you are going to analyze is a module (e.g. Chef cookbook).")
@click.option('--dataset', is_flag=True, default=False,
    help="Use this flag if the folder being analyzed is a dataset. A dataset is a folder with subfolders to be analyzed.")
@click.option('--includeall', multiple=True,
    help="Some files are ignored when analyzing a folder. For instance, sometimes only some" 
         "folders in the folder structure are considered. Use this option if"
         "you want to analyze all the files with a certain extension inside a folder. (e.g. --includeall yml)" 
         "This flag is only relevant if you are using the dataset flag.")
@click.option('--csv', is_flag=True, default=False,
    help="Use this flag if you want the output to be in CSV format.")
@click.option('--autodetect', is_flag=True, default=False,
    help="This flag allows for the automatic detection of the type of script being analyzed. Only relevant for Ansible and when"
         "you are using the dataset flag.")
@click.option('--smells', cls=RulesListOption, default=[], multiple=True, 
    help="The type of smells being analyzed.")
@click.argument('path', type=click.Path(exists=True), required=True)
def analysis(tech, type, path, config, module, csv, dataset, autodetect, includeall, smells):
    parser = None
    if tech == Tech.ansible:
        parser = AnsibleParser()
    elif tech == Tech.chef:
        parser = ChefParser()
    elif tech == Tech.puppet:
        parser = PuppetParser()

    if config == "configs/default.ini":
        config = resource_filename('glitch', "configs/default.ini")

    analyses = []
    rules = RuleVisitor.__subclasses__()
    for r in rules:
        if smells == () or r.get_name() in smells:
            analysis = r(tech)
            analysis.config(config)
            analyses.append(analysis)

    errors = []
    if dataset:
        if includeall != ():
            iac_files = []
            for root, _, files in os.walk(path):
                for name in files:
                    name_split = name.split('.')
                    if len(name_split) == 2 and name_split[-1] in includeall \
                            and not Path(os.path.join(root, name)).is_symlink():
                        iac_files.append(os.path.join(root, name))
            iac_files = set(iac_files)

            for file in iac_files:
                if (autodetect):
                    if "vars" in file or "default" in file:
                        type = "vars"
                    elif "tasks" in file:
                        type = "tasks"
                    else:
                        type = "script"

                inter = parser.parse(file, type, module)
                if inter != None:
                    for analysis in analyses:
                        errors += analysis.check(inter)
        else:
            subfolders = [f.path for f in os.scandir(f"{path}") if f.is_dir()]
            for d in subfolders:
                inter = parser.parse(d, type, module)
                if inter == None: continue
                for analysis in analyses:
                    errors += analysis.check(inter)

        files = [f.path for f in os.scandir(f"{path}") if f.is_file()]
        for file in files:
            if (autodetect):
                if "vars" in file or "default" in file:
                    type = "vars"
                elif "tasks" in file:
                    type = "tasks"
                else:
                    type = "script"
            inter = parser.parse(file, type, module)
            if inter != None:
                for analysis in analyses:
                    errors += analysis.check(inter)
    else:
        inter = parser.parse(path, type, module)
        if inter != None:
            for analysis in analyses:
                errors += analysis.check(inter)
    errors = sorted(set(errors), key=lambda e: (e.path, e.line))
    
    if csv:
        for error in errors:
            print(error.to_csv())
    else:
        for error in errors:
            print(error)

analysis(prog_name='glitch')
