from email.policy import default
import click, os
from thesis.analysis.rules import SecurityVisitor
from thesis.parsers.cmof import AnsibleParser, ChefParser, PuppetParser

@click.command()
@click.option('--tech',
        type=click.Choice(['ansible', 'chef', 'puppet'], case_sensitive=False), required=True)
@click.option('--type',
    type=click.Choice(['script', 'tasks', 'vars'], case_sensitive=False), default='script')
@click.option('--config', type=click.Path(exists=True), default="configs/default.ini")
@click.option('--module', is_flag=True, default=False)
@click.option('--dataset', is_flag=True, default=False)
@click.option('--csv', is_flag=True, default=False)
@click.argument('path', type=click.Path(exists=True), required=True)
def analysis(tech, type, path, config, module, csv, dataset):
    parser = None
    if tech == "ansible":
        parser = AnsibleParser()
    elif tech == "chef":
        parser = ChefParser()
    elif tech == "puppet":
        parser = PuppetParser()

    errors = []
    if dataset:
        subfolders = [f.path for f in os.scandir(f"{path}") if f.is_dir()]
        analysis = SecurityVisitor()
        analysis.config(config)
        for d in subfolders:
            inter = parser.parse(d, type, module)
            if inter == None: continue
            errors += analysis.check(inter)
    else:
        # FIXME Might have performance issues
        inter = parser.parse(path, type, module)
        analysis = SecurityVisitor()
        analysis.config(config)
        if inter != None:
            errors += analysis.check(inter)
    errors = sorted(set(errors), key=lambda e: (e.el.line, e.path))
    
    if csv:
        for error in errors:
            print(error.to_csv())
    else:
        for error in errors:
            print(error)

analysis(prog_name='#TODO')
