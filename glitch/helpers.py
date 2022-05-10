import click
import ast

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
            show_envvar=False, 
            **attrs):
        super().__init__(
            param_decls, 
            show_default, 
            prompt, 
            confirmation_prompt, 
            hide_input, 
            is_flag, 
            flag_value, 
            multiple, 
            count, 
            allow_from_autoenv, 
            type, 
            help, 
            hidden, 
            show_choices, 
            show_envvar, 
            **attrs
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