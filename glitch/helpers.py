import click

from glitch.analysis.rules import RuleVisitor

class RulesListOption(click.Option):
    def __init__(
            self, 
            param_decls=None, 
            show_default=False, 
            prompt=False, 
            confirmation_prompt=False, 
            hide_input=False, is_flag=None, 
            flag_value=None, multiple=False, 
            count=False, 
            allow_from_autoenv=True, 
            type=None, help=None, 
            hidden=False, 
            show_choices=True, 
            show_envvar=False
        ):
        super().__init__(
            param_decls = param_decls,
            show_default = show_default,
            prompt = prompt,
            confirmation_prompt = confirmation_prompt,
            hide_input = hide_input,
            is_flag = is_flag,
            flag_value = flag_value,
            multiple = multiple,
            count = count,
            allow_from_autoenv = allow_from_autoenv,
            type = type,
            help = help,
            hidden = hidden,
            show_choices = show_choices,
            show_envvar = show_envvar,
        )
        rules = list(map(lambda c: c.get_name(), RuleVisitor.__subclasses__()))
        self.type = click.Choice(rules, case_sensitive=False)

def remove_unmatched_brackets(string):
    stack, aux = [], ""

    for c in string:
        if c in ["(", "[", "{"]: 
            stack.append(c)
        elif (len(stack) > 0 
                and (c, stack[-1]) in [(")", "("), ("]", "["), ("}", "{")]):
            stack.pop()
        elif c in [")", "]", "}"]: 
            continue
        aux += c

    i, res = 0, ""
    while (len(stack) > 0 and i < len(aux)):
        if aux[i] == stack[0]:
            stack.pop(0)
            continue
        res += aux[i]
        i += 1
    res += aux[i:]

    return res

# Python program for KMP Algorithm (https://www.geeksforgeeks.org/python-program-for-kmp-algorithm-for-pattern-searching-2/)
# Based on code by Bhavya Jain
def kmp_search(pat, txt):
    M = len(pat)
    N = len(txt)
    res = []
 
    # create lps[] that will hold the longest prefix suffix
    # values for pattern
    lps = [0] * M
    j = 0 # index for pat[]
 
    # Preprocess the pattern (calculate lps[] array)
    compute_LPS_array(pat, M, lps)
 
    i = 0 # index for txt[]
    while i < N:
        if pat[j] == txt[i]:
            i += 1
            j += 1
 
        if j == M:
            res.append(i - j)
            j = lps[j-1]
 
        # mismatch after j matches
        elif i < N and pat[j] != txt[i]:
            # Do not match lps[0..lps[j-1]] characters,
            # they will match anyway
            if j != 0:
                j = lps[j-1]
            else:
                i += 1

    return res
 
def compute_LPS_array(pat, M, lps):
    len = 0 # length of the previous longest prefix suffix
    lps[0]
    i = 1
 
    # the loop calculates lps[i] for i = 1 to M-1
    while i < M:
        if pat[i]== pat[len]:
            len += 1
            lps[i] = len
            i += 1
        else:
            if len != 0:
                len = lps[len-1]
            else:
                lps[i] = 0
                i += 1