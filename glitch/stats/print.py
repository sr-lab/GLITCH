from glob import escape
import pandas as pd
from glitch.analysis.rules import Error
from prettytable import PrettyTable

def print_stats(errors, smells, file_stats, format):
    total_files = len(file_stats.files)
    occurrences = {}
    files_with_the_smell = {'Combined': set()}
    for smell_type in smells:
        for code in Error.ERRORS[smell_type].keys():
            occurrences[code] = 0
            files_with_the_smell[code] = set()

    for error in errors:
        occurrences[error.code] += 1
        files_with_the_smell[error.code].add(error.path)
        files_with_the_smell['Combined'].add(error.path)
        
    stats_info = []
    total_occur = 0
    total_smell_density = 0
    for code, n in occurrences.items():
        total_occur += n
        total_smell_density += round(n / (file_stats.loc / 1000), 2)
        stats_info.append([Error.ALL_ERRORS[code], n, 
            round(n / (file_stats.loc / 1000), 2), 
            round((len(files_with_the_smell[code]) / total_files) * 100, 2)])
    stats_info.append([
        "Combined", 
        total_occur,
        total_smell_density,
        round((len(files_with_the_smell['Combined']) / total_files) * 100, 2)
    ])

    if (format == "prettytable"):
        table = PrettyTable()
        table.field_names = ["Smell", "Occurrences", 
            "Smell density (Smell/KLoC)", "Proportion of scripts (%)"]
        table.align["Smell"] = 'r'
        table.align["Occurrences"] = 'l'
        table.align["Smell density (Smell/KLoC)"] = 'l'
        table.align["Proportion of scripts (%)"] = 'l'
        smells_info = stats_info[:-1]
        for smell in smells_info:
            smell[0] = smell[0].split(' - ')[0]
        smells_info = sorted(smells_info, key=lambda x: x[0])

        biggest_value = [len(name) for name in table.field_names]
        for stats in smells_info:
            for i, s in enumerate(stats):
                if len(str(s)) > biggest_value[i]:
                    biggest_value[i] = len(str(s))

            table.add_row(stats)
        
        div_row = [i * "-" for i in biggest_value]
        table.add_row(div_row)
        table.add_row(stats_info[-1])
        print(table)

        attributes = PrettyTable()
        attributes.field_names = ["Total IaC files", "Lines of Code"]
        attributes.add_row([total_files, file_stats.loc])
        print(attributes)
    elif (format == "latex"):
        smells_info = stats_info[:-1]
        smells_info = sorted(smells_info, key=lambda x: x[0])
        for smell in smells_info:
            smell[0] = smell[0].split(' - ')[0]
        smells_info.append(stats_info[-1])
        table = pd.DataFrame(smells_info, columns = ["\\textbf{Smell}", "\\textbf{Occurrences}", 
            "\\textbf{Smell density (Smell/KLoC)}", "\\textbf{Proportion of scripts (\%)}"])
        latex = table.style.hide(axis='index').format(escape=None, 
                precision=2, thousands=',').to_latex()
        combined = latex[:latex.rfind('\\\\')].rfind('\\\\')
        latex = latex[:combined] + "\\\\\n\midrule\n" + latex[combined + 3:]
        print(latex)

        attributes = pd.DataFrame([[total_files, file_stats.loc]], columns=
            ["\\textbf{Total IaC files}", "\\textbf{Lines of Code}"])
        print(attributes.style.hide(axis='index').format(escape=None, 
                precision=2, thousands=',').to_latex())