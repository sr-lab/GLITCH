from glitch.analysis.rules import Error
from prettytable import PrettyTable

def print_stats(errors, smells, file_stats):
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
        
    occ_table = PrettyTable()
    occ_table.field_names = ["Smell", "Occurrences", 
        "Smell density (Smell/KLoC)", "Proportion of scripts (%)"]
    occ_table.align["Smell"] = 'r'
    occ_table.align["Occurrences"] = 'l'
    occ_table.align["Smell density (Smell/KLoC)"] = 'l'
    occ_table.align["Proportion of scripts (%)"] = 'l'
    occ_table.sortby = "Smell"

    for code, n in occurrences.items():
        occ_table.add_row([Error.ALL_ERRORS[code], n, 
            round(n / (file_stats.loc / 1000), 2), 
            round((len(files_with_the_smell[code]) / total_files) * 100, 1)])
    print(occ_table)

    attributes = PrettyTable()
    attributes.field_names = ["Total IaC files", "Lines of Code"]
    attributes.add_row([total_files, file_stats.loc])
    print(attributes)