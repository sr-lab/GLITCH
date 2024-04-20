import json
import click, os, sys

from pathlib import Path
from typing import Tuple, List, Set, Optional
from glitch.analysis.rules import Error, RuleVisitor
from glitch.helpers import RulesListOption, get_smell_types, get_smells
from glitch.parsers.docker import DockerParser
from glitch.stats.print import print_stats
from glitch.stats.stats import FileStats
from glitch.tech import Tech
from glitch.repr.inter import UnitBlockType
from glitch.parsers.parser import Parser
from glitch.parsers.ansible import AnsibleParser
from glitch.parsers.chef import ChefParser
from glitch.parsers.puppet import PuppetParser
from glitch.parsers.terraform import TerraformParser
from glitch.parsers.gha import GithubActionsParser
from pkg_resources import resource_filename
from alive_progress import alive_bar  # type: ignore


# NOTE: These are necessary in order for python to load the visitors.
# Otherwise, python will not consider these types of rules.
from glitch.analysis.design.visitor import DesignVisitor  # type: ignore
from glitch.analysis.security import SecurityVisitor  # type: ignore


def parse_and_check(
    type: UnitBlockType,
    path: str,
    module: bool,
    parser: Parser,
    analyses: List[RuleVisitor],
    errors: List[Error],
    stats: FileStats,
) -> None:
    inter = parser.parse(path, type, module)
    if inter != None:
        for analysis in analyses:
            errors += analysis.check(inter)
        stats.compute(inter)


def repr_mode(
    type: UnitBlockType,
    path: str,
    module: bool,
    parser: Parser,
) -> None:
    inter = parser.parse(path, type, module)
    if inter != None:
        print(json.dumps(inter.as_dict(), indent=2))


@click.command(
    help="PATH is the file or folder to analyze. OUTPUT is an optional file to which we can redirect the smells output."
)
@click.option(
    "--tech",
    type=click.Choice([t.value for t in Tech]),
    required=True,
    help="The IaC technology in which the scripts analyzed are written in.",
)
@click.option(
    "--tableformat",
    type=click.Choice(("prettytable", "latex")),
    required=False,
    default="prettytable",
    help="The presentation format of the tables that show stats about the run.",
)
@click.option(
    "--type",
    type=click.Choice([t.value for t in UnitBlockType]),
    default=UnitBlockType.unknown,
    help="The type of scripts being analyzed.",
)
@click.option(
    "--config",
    type=click.Path(),
    default="configs/default.ini",
    help="The path for a config file. Otherwise the default config will be used.",
)
@click.option(
    "--module",
    is_flag=True,
    default=False,
    help="Use this flag if the folder you are going to analyze is a module (e.g. Chef cookbook).",
)
@click.option(
    "--dataset",
    is_flag=True,
    default=False,
    help="Use this flag if the folder being analyzed is a dataset. A dataset is a folder with subfolders to be analyzed.",
)
@click.option(
    "--linter",
    is_flag=True,
    default=False,
    help="This flag changes the output to be more usable for other interfaces, such as, extensions for code editors.",
)
@click.option(
    "--includeall",
    multiple=True,
    help="Some files are ignored when analyzing a folder. For instance, sometimes only some"
    "folders in the folder structure are considered. Use this option if"
    "you want to analyze all the files with a certain extension inside a folder. (e.g. --includeall yml)"
    "This flag is only relevant if you are using the dataset flag.",
)
@click.option(
    "--csv",
    is_flag=True,
    default=False,
    help="Use this flag if you want the output to be in CSV format.",
)
@click.option(
    "--smell_types",
    cls=RulesListOption,
    multiple=True,
    help="The type of smell_types being analyzed.",
)
# TODO: Add linter option to here
@click.option(
    "--mode",
    type=click.Choice(["smell_detector", "repr"]),
    help="The mode the tool is running in. If the mode is 'repr', the tool will only print the intermediate representation."
    "The default mode is 'smell_detector'.",
    default="smell_detector",
)
@click.argument("path", type=click.Path(exists=True), required=True)
@click.argument("output", type=click.Path(), required=False)
def glitch(
    tech: str,
    type: str,
    path: str,
    config: str,
    module: bool,
    csv: bool,
    dataset: bool,
    includeall: Tuple[str, ...],
    smell_types: Tuple[str, ...],
    output: Optional[str],
    tableformat: str,
    linter: bool,
    mode: str,
):
    tech = Tech(tech)
    type = UnitBlockType(type)

    if config != "configs/default.ini" and not os.path.exists(config):
        raise click.BadOptionUsage(
            "config", f"Invalid value for 'config': Path '{config}' does not exist."
        )
    elif os.path.isdir(config):
        raise click.BadOptionUsage(
            "config", f"Invalid value for 'config': Path '{config}' should be a file."
        )
    elif config == "configs/default.ini":
        config = resource_filename("glitch", "configs/default.ini")

    parser = None
    if tech == Tech.ansible:
        parser = AnsibleParser()
    elif tech == Tech.chef:
        parser = ChefParser()
    elif tech == Tech.puppet:
        parser = PuppetParser()
    elif tech == Tech.docker:
        parser = DockerParser()
    elif tech == Tech.terraform:
        parser = TerraformParser()
        config = resource_filename("glitch", "configs/terraform.ini")
    elif tech == Tech.gha:
        parser = GithubActionsParser()
    file_stats = FileStats()

    if mode == "repr":
        repr_mode(type, path, module, parser)
        return

    if smell_types == ():
        smell_types = get_smell_types()

    analyses: List[RuleVisitor] = []
    rules = RuleVisitor.__subclasses__()
    for r in rules:
        if smell_types == () or r.get_name() in smell_types:
            analysis = r(tech)
            analysis.config(config)
            analyses.append(analysis)

    errors: List[Error] = []
    if dataset:
        if includeall != ():
            iac_files: Set[str] = set()
            for root, _, files in os.walk(path):
                for name in files:
                    name_split = name.split(".")
                    if (
                        name_split[-1] in includeall
                        and not Path(os.path.join(root, name)).is_symlink()
                    ):
                        iac_files.add(os.path.join(root, name))

            with alive_bar(
                len(iac_files),
                title=f"ANALYZING ALL FILES WITH EXTENSIONS {includeall}",
            ) as bar:  # type: ignore
                for file in iac_files:
                    parse_and_check(
                        type, file, module, parser, analyses, errors, file_stats
                    )
                    bar()
        else:
            subfolders = [f.path for f in os.scandir(f"{path}") if f.is_dir()]
            with alive_bar(len(subfolders), title="ANALYZING SUBFOLDERS") as bar:  # type: ignore
                for d in subfolders:
                    parse_and_check(
                        type, d, module, parser, analyses, errors, file_stats
                    )
                    bar()

        files = [f.path for f in os.scandir(f"{path}") if f.is_file()]

        with alive_bar(len(files), title="ANALYZING FILES IN ROOT FOLDER") as bar:  # type: ignore
            for file in files:
                parse_and_check(
                    type, file, module, parser, analyses, errors, file_stats
                )
                bar()
    else:
        parse_and_check(type, path, module, parser, analyses, errors, file_stats)

    errors = sorted(set(errors), key=lambda e: (e.path, e.line, e.code))

    if output is None:
        f = sys.stdout
    else:
        f = open(output, "w")

    if linter:
        for error in errors:
            print(Error.ALL_ERRORS[error.code] + "," + error.to_csv(), file=f)
    elif csv:
        for error in errors:
            print(error.to_csv(), file=f)
    else:
        for error in errors:
            print(error, file=f)

    if f != sys.stdout:
        f.close()
    if not linter:
        print_stats(errors, get_smells(smell_types, tech), file_stats, tableformat)


def main() -> None:
    glitch(prog_name="glitch")


main()
