import pandas as pd  # type: ignore
from prettytable import PrettyTable
from typing import List, Dict, Set, Tuple
from glitch.analysis.rules import Error
from glitch.stats.stats import FileStats


def print_stats(
    errors: List[Error], smells: List[str], file_stats: FileStats, format: str
) -> None:
    total_files = len(file_stats.files)
    occurrences: Dict[str, int] = {}
    files_with_the_smell: Dict[str, Set[str]] = {"Combined": set()}

    for smell in smells:
        occurrences[smell] = 0
        files_with_the_smell[smell] = set()

    for error in errors:
        occurrences[error.code] += 1
        files_with_the_smell[error.code].add(error.path)
        files_with_the_smell["Combined"].add(error.path)

    stats_info: List[Tuple[str, int, float, float]] = []
    total_occur = 0
    total_smell_density = 0
    for code, n in occurrences.items():
        total_occur += n
        total_smell_density += round(n / (max(1, file_stats.loc) / 1000), 2)
        stats_info.append(
            (
                Error.ALL_ERRORS[code],
                n,
                round(n / (max(1, file_stats.loc) / 1000), 2),
                round((len(files_with_the_smell[code]) / max(1, total_files)) * 100, 2),
            )
        )
    stats_info.append(
        (
            "Combined",
            total_occur,
            total_smell_density,
            round(
                (len(files_with_the_smell["Combined"]) / max(1, total_files)) * 100, 2
            ),
        )
    )

    if format == "prettytable":
        table = PrettyTable()
        table.field_names = [
            "Smell",
            "Occurrences",
            "Smell density (Smell/KLoC)",
            "Proportion of scripts (%)",
        ]

        table.align["Smell"] = "r"  # type: ignore
        table.align["Occurrences"] = "l"  # type: ignore
        table.align["Smell density (Smell/KLoC)"] = "l"  # type: ignore
        table.align["Proportion of scripts (%)"] = "l"  # type: ignore
        smells_info = stats_info[:-1]

        smells_info = map(
            lambda smell: (smell[0].split(" - ")[0], smell[1], smell[2], smell[3]),
            smells_info,
        )
        smells_info = sorted(smells_info, key=lambda x: x[0])

        biggest_value = [len(name) for name in table.field_names]
        for stats in smells_info:
            for i, s in enumerate(stats):
                if len(str(s)) > biggest_value[i]:
                    biggest_value[i] = len(str(s))

            table.add_row(stats)  # type: ignore

        div_row = [i * "-" for i in biggest_value]
        table.add_row(div_row)  # type: ignore
        table.add_row(stats_info[-1])  # type: ignore
        print(table)

        attributes = PrettyTable()
        attributes.field_names = ["Total IaC files", "Lines of Code"]
        attributes.add_row([total_files, file_stats.loc])  # type: ignore
        print(attributes)
    elif format == "latex":
        smells_info = stats_info[:-1]
        smells_info = sorted(smells_info, key=lambda x: x[0])
        smells_info = list(
            map(
                lambda smell: (smell[0].split(" - ")[0], smell[1], smell[2], smell[3]),
                smells_info,
            )
        )
        smells_info.append(stats_info[-1])
        table = pd.DataFrame(
            smells_info,
            columns=[
                "\\textbf{Smell}",
                "\\textbf{Occurrences}",
                "\\textbf{Smell density (Smell/KLoC)}",
                "\\textbf{Proportion of scripts (%)}",
            ],
        )
        latex = (  # type: ignore
            table.style.hide(axis="index")  # type: ignore
            .format(escape=None, precision=2, thousands=",")  # type: ignore
            .to_latex()  # type: ignore
        )
        combined = latex[: latex.rfind("\\\\")].rfind("\\\\")  # type: ignore
        latex = latex[:combined] + "\\\\\n\\midrule\n" + latex[combined + 3 :]  # type: ignore
        print(latex)  # type: ignore

        attributes = pd.DataFrame(
            [[total_files, file_stats.loc]],
            columns=["\\textbf{Total IaC files}", "\\textbf{Lines of Code}"],  # type: ignore
        )
        print(
            attributes.style.hide(axis="index")  # type: ignore
            .format(escape=None, precision=2, thousands=",")  # type: ignore
            .to_latex()  # type: ignore
        )
