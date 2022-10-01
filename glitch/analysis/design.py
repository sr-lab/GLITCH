from cmath import inf
import json
import re
import configparser
from glitch.analysis.rules import Error, RuleVisitor, SmellChecker
from glitch.tech import Tech

from glitch.repr.inter import *

class DesignVisitor(RuleVisitor):
    class ImproperAlignmentSmell(SmellChecker):
        def check(self, element, file: str):
            if isinstance(element, AtomicUnit):
                identation = None
                for a in element.attributes:
                    first_line = a.code.split("\n")[0]
                    curr_id = len(first_line) - len(first_line.lstrip())

                    if (identation is None):
                        identation = curr_id
                    elif (identation != curr_id):
                        return [Error('implementation_improper_alignment', 
                            element, file, repr(element))]

                return []
            return []

    class PuppetImproperAlignmentSmell(SmellChecker):
        cached_file = ""
        lines = []

        def check(self, element, file: str) -> list[Error]:
            if DesignVisitor.PuppetImproperAlignmentSmell.cached_file != file:
                with open(file, "r") as f:
                    DesignVisitor.PuppetImproperAlignmentSmell.lines = f.readlines()
                    DesignVisitor.PuppetImproperAlignmentSmell.cached_file = file
            lines = DesignVisitor.PuppetImproperAlignmentSmell.lines

            longest = 0
            longest_ident = 0
            longest_split = ""
            for a in element.attributes:
                if len(a.name) > longest and '=>' in a.code:
                    longest = len(a.name)
                    split = lines[a.line - 1].split('=>')[0]
                    longest_ident = len(split)
                    longest_split = split
            if longest_split == "": return []
            elif len(longest_split) - 1 != len(longest_split.rstrip()):
                return [Error('implementation_improper_alignment', 
                    element, file, repr(element))]

            for a in element.attributes:
                first_line = lines[a.line - 1]
                cur_arrow_column = len(first_line.split('=>')[0])
                if cur_arrow_column != longest_ident:
                    return [Error('implementation_improper_alignment', 
                            element, file, repr(element))]

            return []
    
    class AnsibleImproperAlignmentSmell(SmellChecker):
        # YAML does not allow improper alignments (it also would have problems with generic attributes for all modules)
        def check(self, element: AtomicUnit, file: str):
            return []

    class MisplacedAttribute(SmellChecker):
        def check(self, element, file: str):
            return []

    class ChefMisplacedAttribute(SmellChecker):
        def check(self, element, file: str):
            if isinstance(element, AtomicUnit):
                order = []
                for attribute in element.attributes:
                    if attribute.name == "source":
                        order.append(1)
                    elif attribute.name in ["owner", "group"]:
                        order.append(2)
                    elif attribute.name == "mode":
                        order.append(3)
                    elif attribute.name == "action":
                        order.append(4)

                if order != sorted(order):
                    return [Error('design_misplaced_attribute', element, file, repr(element))]
            return []

    class PuppetMisplacedAttribute(SmellChecker):
        def check(self, element, file: str):
            if isinstance(element, AtomicUnit):
                for i, attr in enumerate(element.attributes):
                    if attr.name == "ensure" and i != 0:
                        return [Error('design_misplaced_attribute', element, file, repr(element))]
            elif isinstance(element, UnitBlock):
                optional = False
                for attr in element.attributes:
                    if attr.value is not None:
                        optional = True
                    elif optional == True:
                        return [Error('design_misplaced_attribute', element, file, repr(element))]
            return []

    def __init__(self, tech: Tech) -> None:
        super().__init__(tech)

        if tech == Tech.ansible:
            self.imp_align = DesignVisitor.AnsibleImproperAlignmentSmell()
        elif tech == Tech.puppet:
            self.imp_align = DesignVisitor.PuppetImproperAlignmentSmell()
        else:
            self.imp_align = DesignVisitor.ImproperAlignmentSmell()

        if tech == Tech.chef:
            self.misplaced_attr = DesignVisitor.ChefMisplacedAttribute()
        elif tech == Tech.puppet:
            self.misplaced_attr = DesignVisitor.PuppetMisplacedAttribute()
        else:
            self.misplaced_attr = DesignVisitor.MisplacedAttribute()

        if tech in [Tech.chef, Tech.puppet, Tech.ansible]:
            self.comment = "#"
        else:
            self.comment = "//"

        self.variable_stack = []
        self.variables_names = []
        self.first_code_line = inf

    @staticmethod
    def get_name() -> str:
        return "design"

    def config(self, config_path: str):
        config = configparser.ConfigParser()
        config.read(config_path)
        DesignVisitor.__EXEC = json.loads(config['design']['exec_atomic_units'])
        DesignVisitor.__DEFAULT_VARIABLES = json.loads(config['design']['default_variables'])
        if 'var_refer_symbol' not in config['design']:
            DesignVisitor.__VAR_REFER_SYMBOL = None
        else:
            DesignVisitor.__VAR_REFER_SYMBOL = json.loads(config['design']['var_refer_symbol'])

    def check_module(self, m: Module) -> list[Error]:
        errors = super().check_module(m)
        # FIXME Needs to consider more things
        # if len(m.blocks) == 0:
        #     errors.append(Error('design_unnecessary_abstraction', m, m.path, repr(m)))
        return errors

    def check_unitblock(self, u: UnitBlock) -> list[Error]:
        def count_atomic_units(ub: UnitBlock):
            count_resources = len(ub.atomic_units)
            count_execs = 0
            for au in ub.atomic_units:
                if au.type in DesignVisitor.__EXEC:
                    count_execs += 1
            
            for unitblock in ub.unit_blocks:
                resources, execs = count_atomic_units(unitblock)
                count_resources += resources
                count_execs += execs

            return count_resources, count_execs

        with open(u.path, "r") as f:
            try:
                code_lines = f.readlines()
                f.seek(0, 0)
                all_code = f.read()
                code = ""
            except UnicodeDecodeError:
                return []

        self.first_non_comm_line = inf
        for i, line in enumerate(code_lines):
            if not line.startswith(self.comment): 
                self.first_non_comm_line = i + 1
                break 

        self.variable_stack.append(len(self.variables_names))
        for attr in u.attributes:
           self.variables_names.append(attr.name)

        errors = []
        # The order is important
        for au in u.atomic_units:
            errors += self.check_atomicunit(au, u.path)
        for v in u.variables:
            errors += self.check_variable(v, u.path)
        for a in u.attributes:
            errors += self.check_attribute(a, u.path)
        for d in u.dependencies:
            errors += self.check_dependency(d, u.path)
        for s in u.statements:
            errors += self.check_element(s, u.path)
        for c in u.comments:
            errors += self.check_comment(c, u.path)

        total_resources, total_execs = count_atomic_units(u)

        if total_execs > 2 and (total_execs / total_resources) > 0.20:
            errors.append(Error('design_imperative_abstraction', u, u.path, repr(u)))

        for i, line in enumerate(code_lines):
            if ("\t" in line):
                error = Error('implementation_improper_alignment', 
                    u, u.path, repr(u))
                error.line = i + 1
                errors.append(error)
            if len(line) > 140:
                error = Error('implementation_long_statement', u, u.path, line)
                error.line = i + 1
                errors.append(error)
        
        # The UnitBlock should not be of type vars, because these files are supposed to only
        # have variables
        if len(u.variables) / max(len(code_lines), 1) > 0.3 and u.type != UnitBlockType.vars:
            errors.append(Error('implementation_too_many_variables', u, u.path, repr(u)))

        if DesignVisitor.__VAR_REFER_SYMBOL is not None:
            # FIXME could be improved if we considered strings as part of the model
            for i, l in enumerate(code_lines):
                for tuple in re.findall(r'(\'([^\\]|(\\(\n|.)))*?\')|(\"([^\\]|(\\(\n|.)))*?\")', l):
                    for string in (tuple[0], tuple[4]):
                        for var in self.variables_names + DesignVisitor.__DEFAULT_VARIABLES:
                            if (DesignVisitor.__VAR_REFER_SYMBOL + var) in string[1:-1]:
                                error = Error('implementation_unguarded_variable', u, u.path, string)
                                error.line = i + 1
                                errors.append(error)

        def get_line(i ,lines):
            for j, line in lines:
                if i < j:
                    return line

        lines = []
        current_line = 1
        i = 0
        for c in all_code:
            if c == '\n':
                lines.append((i, current_line))
                current_line += 1
            elif not c.isspace():
                code += c
                i += 1
        lines.append((i, current_line))

        blocks = {}
        for i in range(len(code) - 150):
            hash = code[i : i + 150].__hash__()
            if hash not in blocks:
                blocks[hash] = [i]
            else:
                blocks[hash].append(i)

        # Note: changing the structure to a set instead of a list increased the speed A LOT
        checked = set()
        for _, value in blocks.items():
            if len(value) >= 2:
                for i in value:
                    if i not in checked:
                        line = get_line(i, lines)
                        error = Error('design_duplicate_block', u, u.path, code_lines[line - 1])
                        error.line = line
                        errors.append(error)
                        checked.update(range(i, i + 150))

        # FIXME Needs to consider more things
        # if (len(u.statements) == 0 and len(u.atomic_units) == 0 and
        #         len(u.variables) == 0 and len(u.unit_blocks) == 0 and
        #             len(u.attributes) == 0):
        #     errors.append(Error('design_unnecessary_abstraction', u, u.path, repr(u)))

        errors += self.misplaced_attr.check(u, u.path)
        errors += self.imp_align.check(u, u.path)

        # The unit blocks inside should only be considered after in order to
        # have the correct variables
        for ub in u.unit_blocks:
            errors += self.check_unitblock(ub)

        variable_size = self.variable_stack.pop()
        if (variable_size == 0): self.variables_names = []
        else: self.variables_names = self.variables_names[:variable_size]

        return errors

    def check_condition(self, c: ConditionStatement, file: str) -> list[Error]:
        return super().check_condition(c, file)

    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        errors = super().check_atomicunit(au, file)
        errors += self.imp_align.check(au, file)
        errors += self.misplaced_attr.check(au, file)

        if au.type in DesignVisitor.__EXEC:
            if ("&&" in au.name or ";" in au.name or "|" in au.name):
                errors.append(Error("design_multifaceted_abstraction", au, file, repr(au)))
            else:
                for attribute in au.attributes:
                    value = repr(attribute.value)
                    if ("&&" in value or ";" in value or "|" in value):
                        errors.append(Error("design_multifaceted_abstraction", au, file, repr(au)))
                        break


        if au.type in DesignVisitor.__EXEC:
            lines = 0
            for attr in au.attributes:
                for line in attr.code.split('\n'):
                    if line.strip() != "": lines += 1

            if lines > 7: 
                errors.append(Error("design_long_resource", au, file, repr(au)))

        return errors

    def check_dependency(self, d: Dependency, file: str) -> list[Error]:
        return []

    def check_attribute(self, a: Attribute, file: str) -> list[Error]:
        return []

    def check_variable(self, v: Variable, file: str) -> list[Error]:
        self.variables_names.append(v.name)
        return []

    def check_comment(self, c: Comment, file: str) -> list[Error]:
        errors = []
        if c.line >= self.first_non_comm_line:
            errors.append(Error('design_avoid_comments', c, file, repr(c)))
        return errors