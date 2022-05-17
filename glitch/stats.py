from glitch.analysis.rules import Error
from prettytable import PrettyTable

def print_stats(errors, smells):
    occurrences = {}
    for smell_type in smells:
        for code in Error.ERRORS[smell_type].keys():
            occurrences[code] = 0

    for error in errors:
        occurrences[error.code] += 1

    occ_table = PrettyTable()
    occ_table.field_names = ["Smell", "Occurrences"]
    for code, n in occurrences.items():
        occ_table.add_row([Error.ALL_ERRORS[code], n])
    print(occ_table)