import pandas as pd
from glitch.analysis.rules import Error
from prettytable import PrettyTable

def print_stats(errors, smells, file_stats, format):
    total_files = len(file_stats.files)
    occurrences = {}
    files_with_the_smell = {}
    for smell_type in smells:
        for code in Error.ERRORS[smell_type].keys():
            occurrences[code] = 0
            files_with_the_smell[code] = set()

    for error in errors:
        occurrences[error.code] += 1
        files_with_the_smell[error.code].add(error.path)
        
    stats_info = []
    for code, n in occurrences.items():
        stats_info.append([Error.ALL_ERRORS[code], n, 
            round(n / (file_stats.loc / 1000), 2), 
            round((len(files_with_the_smell[code]) / total_files) * 100, 1)])

    if (format == "prettytable"):
        table = PrettyTable()
        table.field_names = ["Smell", "Occurrences", 
            "Smell density (Smell/KLoC)", "Proportion of scripts (%)"]
        table.align["Smell"] = 'r'
        table.align["Occurrences"] = 'l'
        table.align["Smell density (Smell/KLoC)"] = 'l'
        table.align["Proportion of scripts (%)"] = 'l'
        table.sortby = "Smell"

        for stats in stats_info:
            table.add_row(stats)
        print(table)

        attributes = PrettyTable()
        attributes.field_names = ["Total IaC files", "Lines of Code"]
        attributes.add_row([total_files, file_stats.loc])
        print(attributes)
    elif (format == "latex"):
        table = pd.DataFrame(stats_info, columns = ["\\textbf{Smell}", "\\textbf{Occurrences}", 
            "\\textbf{Smell density (Smell/KLoC)}", "\\textbf{Proportion of scripts (\%)}"])
        print(table.to_latex(index=False, escape=False))

        attributes = pd.DataFrame([[total_files, file_stats.loc]], columns=
            ["\\textbf{Total IaC files}", "\\textbf{Lines of Code}"])
        print(attributes.to_latex(index=False, escape=False))