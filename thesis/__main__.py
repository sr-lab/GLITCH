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
            analysis = SecurityVisitor()
            errors += sorted(analysis.check(inter), key=lambda e: (e.path, e.el.line))
    else:
         # FIXME Might have performance issues
        inter = parser.parse(path, module)
        analysis = SecurityVisitor()
        errors += sorted(analysis.check(inter), key=lambda e: (e.path, e.el.line))
    errors = set(errors)
    
    if csv:
        for error in errors:
            print(error.to_csv())
    else:
        for error in errors:
            print(error)

analysis(prog_name='#TODO')
