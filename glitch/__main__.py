import json
import tqdm
import click, os, sys

from pathlib import Path
from typing import Tuple, List, Set, Optional, TextIO, Dict
from glitch.analysis.rules import Error, RuleVisitor
from glitch.helpers import get_smell_types, get_smells
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
from glitch.exceptions import throw_exception
from pkg_resources import resource_filename
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor, Future, as_completed


# NOTE: These are necessary in order for python to load the visitors.
# Otherwise, python will not consider these types of rules.
from glitch.analysis.design.visitor import DesignVisitor  # type: ignore
from glitch.analysis.security import SecurityVisitor  # type: ignore


def __parse_and_check(
    type: UnitBlockType,
    path: str,
    module: bool,
    parser: Parser,
    analyses: List[RuleVisitor],
    stats: FileStats,
) -> Set[Error]:
    errors: Set[Error] = set()
    inter = parser.parse(path, type, module)
    # Avoids problems with multiple threads (and possibly multiple files)
    # sharing the same object
    analyses = deepcopy(analyses)

    if inter != None:
        for analysis in analyses:
            errors.update(analysis.check(inter))
        stats.compute(inter)

    return errors


def __print_errors(errors: Set[Error], f: TextIO, linter: bool, csv: bool) -> None:
    errors_sorted = sorted(errors, key=lambda e: (e.path, e.line, e.code))
    if linter:
        for error in errors_sorted:
            print(Error.ALL_ERRORS[error.code] + "," + error.to_csv(), file=f)
    elif csv:
        for error in errors_sorted:
            print(error.to_csv(), file=f)
    else:
        for error in errors_sorted:
            print(error, file=f)


def __get_parser(tech: Tech) -> Parser:
    if tech == Tech.ansible:
        return AnsibleParser()
    elif tech == Tech.chef:
        return ChefParser()
    elif tech == Tech.puppet:
        return PuppetParser()
    elif tech == Tech.docker:
        return DockerParser()
    elif tech == Tech.terraform:
        return TerraformParser()
    elif tech == Tech.gha:
        return GithubActionsParser()
    else:
        raise ValueError(f"Invalid tech: {tech}")


def __get_paths_and_title(
    folder_strategy: str, path: str, tech: Tech
) -> Tuple[Set[str], str]:
    paths: Set[str] = set()
    title = ""

    if folder_strategy == "dataset":
        paths = set([f.path for f in os.scandir(f"{path}") if f.is_dir()])
        title = "ANALYZING SUBFOLDERS"
    elif folder_strategy == "include-all":
        extensions = tech.extensions
        for root, _, files in os.walk(path):
            for name in files:
                name_split = name.split(".")
                if (
                    name_split[-1] in extensions
                    and not Path(os.path.join(root, name)).is_symlink()
                ):
                    paths.add(os.path.join(root, name))
        title = f"ANALYZING ALL FILES WITH EXTENSIONS {extensions}"
    elif folder_strategy == "project":
        paths.add(path)
        title = "ANALYZING PROJECT"
    elif folder_strategy == "module":
        paths.add(path)
        title = "ANALYZING MODULE"

    return paths, title


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
    type=click.Choice([t.tech for t in Tech]),
    required=True,
    help="The IaC technology to be considered.",
)
@click.option(
    "--table-format",
    type=click.Choice(("prettytable", "latex")),
    required=False,
    default="prettytable",
    help="The presentation format of the tables that summarize the run.",
)
@click.option(
    "--type",
    type=click.Choice([t.value for t in UnitBlockType]),
    default=UnitBlockType.unknown,
    help="The type of the scripts being analyzed.",
)
@click.option(
    "--config",
    type=click.Path(),
    default="configs/default.ini",
    help="The path for a config file. Otherwise the default config is used.",
)
@click.option(
    "--folder-strategy",
    type=click.Choice(["project", "module", "dataset", "include-all"]),
    default="project",
    help="The method used to handle the folder (if the path is a folder). "
    "If 'project', the folder is parsed and analyzed as a Project construct. "
    "If 'module', the folder is parsed and analyzed as a Module construct. "
    "If 'dataset', each subfolder in the root folder is analyzed as a Project construct. "
    "If 'include-all', all files inside the folder and its subfolders, and which extensions correspond to the technology being considered, are analyzed individually"
    " (e.g. .yml and .yaml files for Ansible). "
    "Defaults to 'project'.",
)
@click.option(
    "--linter",
    is_flag=True,
    default=False,
    help="Changes the output to be more usable for other interfaces, such as, extensions for code editors.",
)
@click.option(
    "--csv",
    is_flag=True,
    default=False,
    help="Changes the output to CSV format.",
)
@click.option(
    "--smell-types",
    type=click.Choice(get_smell_types(), case_sensitive=False),
    multiple=True,
    help="The type of smell_types being analyzed.",
)
@click.option(
    "--mode",
    type=click.Choice(["smell_detector", "repr"]),
    help="The mode the tool is running in. If the mode is 'repr', the output is the intermediate representation."
    "Defaults to 'smell_detector'.",
    default="smell_detector",
)
@click.option(
    "--n-workers",
    type=int,
    help="Number of parallel workers to use. Defaults to 1.",
    default=1,
)
@click.argument("path", type=click.Path(exists=True), required=True)
@click.argument("output", type=click.Path(), required=False)
def glitch(
    tech: str,  # type: ignore
    type: str,
    path: str,
    folder_strategy: str,
    config: str,
    csv: bool,
    smell_types: Tuple[str, ...],
    output: Optional[str],
    table_format: str,
    linter: bool,
    mode: str,
    n_workers: int,
):
    for t in Tech:
        if t.tech == tech:
            tech: Tech = t
            break
    else:
        raise click.BadOptionUsage(
            "tech",
            f"Invalid value for 'tech': '{tech}' is not a valid technology.",
        )

    type = UnitBlockType(type)
    module = folder_strategy == "module"

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

    parser = __get_parser(tech)
    if tech == Tech.terraform:
        config = resource_filename("glitch", "configs/terraform.ini")
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
    paths: Set[str]
    title: str
    paths, title = __get_paths_and_title(folder_strategy, path, tech)
    futures: List[Future[Set[Error]]] = []
    future_to_path: Dict[Future[Set[Error]], str] = {}
    executor = ThreadPoolExecutor(max_workers=n_workers)

    for p in paths:
        futures.append(
            executor.submit(
                __parse_and_check, type, p, module, parser, analyses, file_stats
            )
        )
        future_to_path[futures[-1]] = p

    f = sys.stdout if output is None else open(output, "w")
    for future in tqdm.tqdm(as_completed(futures), total=len(futures), desc=title):
        try:
            new_errors = future.result()
            errors.extend(new_errors)
            __print_errors(new_errors, f, linter, csv)
        except:
            throw_exception("Unknown Error: {}", future_to_path[future])
    if f != sys.stdout:
        f.close()

    if not linter:
        print_stats(errors, get_smells(smell_types, tech), file_stats, table_format)


def main() -> None:
    glitch(prog_name="glitch")


if __name__ == "__main__":
    main()
