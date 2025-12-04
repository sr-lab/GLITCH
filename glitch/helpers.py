from typing import List, Tuple, Iterable, Dict
from glitch.tech import Tech
from glitch.analysis.rules import Error
import configparser

def get_smell_types() -> Tuple[str, ...]:
    """Get list of smell types.

    Returns:
        List[str]: List of smell types.
    """
    return tuple(Error.ERRORS.keys())


def get_smells(smell_types: Iterable[str], tech: Tech) -> List[str]:
    """Get list of smells.

    Args:
        smell_types (List[str]): List of smell types.
        tech (Tech): Technology being analyzed.

    Returns:
        List[str]: List of smells.
    """

    smells: List[str] = []
    for smell_type in smell_types:
        errors = Error.ERRORS[smell_type]
        for error in errors:
            if error == tech:
                smells.extend(errors[error].keys())  # type: ignore
            elif not isinstance(error, Tech):
                smells.append(error)
    return smells


def remove_unmatched_brackets(string: str):
    stack: List[str] = []
    aux = ""

    for c in string:
        if c in ["(", "[", "{"]:
            stack.append(c)
        elif len(stack) > 0 and (c, stack[-1]) in [(")", "("), ("]", "["), ("}", "{")]:
            stack.pop()
        elif c in [")", "]", "}"]:
            continue
        aux += c

    i, res = 0, ""
    while len(stack) > 0 and i < len(aux):
        if aux[i] == stack[0]:
            stack.pop(0)
            continue
        res += aux[i]
        i += 1
    res += aux[i:]

    return res


# Python program for KMP Algorithm (https://www.geeksforgeeks.org/python-program-for-kmp-algorithm-for-pattern-searching-2/)
# Based on code by Bhavya Jain
def kmp_search(pat: str, txt: str):
    M = len(pat)
    N = len(txt)
    res: List[int] = []

    # create lps[] that will hold the longest prefix suffix
    # values for pattern
    lps = [0] * M
    j = 0  # index for pat[]

    # Preprocess the pattern (calculate lps[] array)
    compute_LPS_array(pat, M, lps)

    i = 0  # index for txt[]
    while i < N:
        if pat[j] == txt[i]:
            i += 1
            j += 1

        if j == M:
            res.append(i - j)
            j = lps[j - 1]

        # mismatch after j matches
        elif i < N and pat[j] != txt[i]:
            # Do not match lps[0..lps[j-1]] characters,
            # they will match anyway
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1

    return res


def compute_LPS_array(pat: str, M: int, lps: List[int]) -> None:
    len = 0  # length of the previous longest prefix suffix
    lps[0]
    i = 1

    # the loop calculates lps[i] for i = 1 to M-1
    while i < M:
        if pat[i] == pat[len]:
            len += 1
            lps[i] = len
            i += 1
        else:
            if len != 0:
                len = lps[len - 1]
            else:
                lps[i] = 0
                i += 1

def ini_to_json_dict(config_path: str) -> Dict[str, Dict[str, List[str]]]:
    config = configparser.ConfigParser()
    config.read(config_path)

    result: Dict[str, Dict[str, List[str]]] = {}

    for section in config.sections():
        section_data = {}

        for key, value in config.items(section):
            parsed = value.strip()

            # Case: empty list
            if parsed == "":
                section_data[key] = []
                continue

            # Case: list inside brackets: ["a", "b"]
            if parsed.startswith("[") and parsed.endswith("]"):
                inner = parsed[1:-1].strip()
                if inner == "":
                    section_data[key] = []
                else:
                    section_data[key] = [
                        item.strip().strip('"').strip("'")
                        for item in inner.split(",")
                    ]
            else:
                # Case: plain value, keep as string
                section_data[key] = parsed

        result[section] = section_data

    return result