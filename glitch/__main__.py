import click, os
from glitch.analysis.rules import RuleVisitor
from glitch.helpers import RulesListOption
from glitch.parsers.cmof import AnsibleParser, ChefParser, PuppetParser
from pkg_resources import resource_filename
from pathlib import Path

# NOTE: There are necessary in order for python to load the visitors
from glitch.analysis.design import DesignVisitor 
from glitch.analysis.security import SecurityVisitor

@click.command()
@click.option('--tech',
        type=click.Choice(['ansible', 'chef', 'puppet'], case_sensitive=False), required=True)
@click.option('--type',
    type=click.Choice(['script', 'tasks', 'vars'], case_sensitive=False), default='script')
@click.option('--config', type=click.Path(), default="configs/default.ini")
@click.option('--module', is_flag=True, default=False)
@click.option('--dataset', is_flag=True, default=False)
@click.option('--includeall', multiple=True)
@click.option('--csv', is_flag=True, default=False)
@click.option('--autodetect', is_flag=True, default=False)
@click.option('--smells', cls=RulesListOption, default=[], multiple=True)
@click.argument('path', type=click.Path(exists=True), required=True)
def analysis(tech, type, path, config, module, csv, dataset, autodetect, includeall, smells):
    parser = None
    if tech == "ansible":
        parser = AnsibleParser()
    elif tech == "chef":
        parser = ChefParser()
    elif tech == "puppet":
        parser = PuppetParser()

    if config == "configs/default.ini":
        config = resource_filename('glitch', "configs/default.ini")

    analyses = []
    rules = RuleVisitor.__subclasses__()
    for r in rules:
        if smells == () or r.get_name() in smells:
            analysis = r()
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
