import click, os
from thesis.analysis.rules import SecurityVisitor
from thesis.parsers.cmof import AnsibleParser, ChefParser

@click.command()
@click.option('--tech',
        type=click.Choice(['ansible', 'chef'], case_sensitive=False), required=True)
@click.option('--module', is_flag=True, default=False)
@click.option('--dataset', is_flag=True, default=False)
@click.option('--csv', is_flag=True, default=False)
@click.argument('path', type=click.Path(exists=True), required=True)
def analysis(tech, path, module, csv, dataset):
    parser = None
    if tech == "ansible":
        parser = AnsibleParser()
    elif tech == "chef":
        parser = ChefParser()

    errors = []
    if dataset:
        subfolders = [f.path for f in os.scandir(f"{path}") if f.is_dir()]
        for d in subfolders:
            inter = parser.parse(d, module)
            if inter == None: continue
            analysis = SecurityVisitor()
            errors += analysis.check(inter)
    else:
         # FIXME Might have performance issues
        inter = parser.parse(path, module)
        if inter != None:
            analysis = SecurityVisitor()
            errors += analysis.check(inter)
    errors = sorted(set(errors), key=lambda e: (e.el.line, e.path))
    
    if csv:
        for error in errors:
            print(error.to_csv())
    else:
        for error in errors:
            print(error)

analysis(prog_name='#TODO')
