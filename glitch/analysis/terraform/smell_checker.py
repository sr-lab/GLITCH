import os
import re
from typing import List, Callable
from glitch.repr.inter import *
from glitch.analysis.rules import Error, SmellChecker

class TerraformSmellChecker(SmellChecker):
    def get_au(self, c, file: str, name: str, type: str):
        if isinstance(c, Project):
            module_name = os.path.basename(os.path.dirname(file))
            for m in c.modules:
                if m.name == module_name:
                    return self.get_au(m, file, name, type)
        elif isinstance(c, Module):
            for ub in c.blocks:
                au = self.get_au(ub, file, name, type)
                if au is not None:
                    return au
        elif isinstance(c, UnitBlock):
            for au in c.atomic_units:
                if (au.type == type and au.name == name):
                    return au
        return None

    def get_associated_au(self, code, file: str, type: str, attribute_name: str , pattern, attribute_parents: list):
        if isinstance(code, Project):
            module_name = os.path.basename(os.path.dirname(file))
            for m in code.modules:
                if m.name == module_name:
                    return self.get_associated_au(m, file, type, attribute_name, pattern, attribute_parents)
        elif isinstance(code, Module):
            for ub in code.blocks:
                au = self.get_associated_au(ub, file, type, attribute_name, pattern, attribute_parents)
                if au is not None:
                    return au
        elif isinstance(code, UnitBlock):
            for au in code.atomic_units:
                if (au.type == type and self.check_required_attribute(
                        au.attributes, attribute_parents, attribute_name, None, pattern)):
                    return au
        return None
    
    def get_attributes_with_name_and_value(self, attributes, parents, name, value = None, pattern = None):
        aux = []
        for a in attributes:
            if a.name.split('dynamic.')[-1] == name and parents == [""]:
                if ((value and a.value.lower() == value) or (pattern and re.match(pattern, a.value.lower()))):
                    aux.append(a)
                elif ((value and a.value.lower() != value) or (pattern and not re.match(pattern, a.value.lower()))):
                    continue
                elif (not value and not pattern):
                    aux.append(a)
            elif a.name.split('dynamic.')[-1] in parents:
                aux += self.get_attributes_with_name_and_value(a.keyvalues, [""], name, value, pattern)
            elif a.keyvalues != []:
                aux += self.get_attributes_with_name_and_value(a.keyvalues, parents, name, value, pattern)
        return aux

    def check_required_attribute(self, attributes, parents, name, value = None, pattern = None, return_all = False):
        attributes = self.get_attributes_with_name_and_value(attributes, parents, name, value, pattern)
        if attributes != []:
            if return_all:
                return attributes
            return attributes[0]
        else:
            return None
        
    def check_database_flags(self, au: AtomicUnit, file: str, smell: str, flag_name: str, safe_value: str, 
                                required_flag = True):
        database_flags = self.get_attributes_with_name_and_value(au.attributes, ["settings"], "database_flags")
        found_flag = False
        errors = []
        if database_flags != []:
            for flag in database_flags:
                name = self.check_required_attribute(flag.keyvalues, [""], "name", flag_name)
                if name is not None:
                    found_flag = True
                    value = self.check_required_attribute(flag.keyvalues, [""], "value")
                    if value and value.value.lower() != safe_value:
                        errors.append(Error(smell, value, file, repr(value)))
                        break
                    elif not value and required_flag:
                        errors.append(Error(smell, flag, file, repr(flag), 
                            f"Suggestion: check for a required attribute with name 'value'."))
                        break
        if not found_flag and required_flag:
            errors.append(Error(smell, au, file, repr(au), 
                f"Suggestion: check for a required flag '{flag_name}'."))
        return errors
    
    def iterate_required_attributes(
        self, attributes: List[KeyValue], name: str, check: Callable[[KeyValue], bool]
    ):
        i = 0
        attribute = self.check_required_attribute(attributes, [""], f"{name}[{i}]")

        while attribute:
            if check(attribute):
                return True, attribute
            i += 1
            attribute = self.check_required_attribute(attributes, [""], f"{name}[{i}]")

        return False, None