import os
import re

from re import Pattern
from typing import Optional, List, Callable, Any
from glitch.repr.inter import *
from glitch.analysis.rules import Error, SmellChecker


class TerraformSmellChecker(SmellChecker):
    def get_au(
        self,
        file: str,
        name: str,
        type: str,
        c: Project | Module | UnitBlock | None = None,
    ) -> Optional[AtomicUnit]:
        c = self.code if c is None else c
        if isinstance(c, Project):
            module_name = os.path.basename(os.path.dirname(file))
            for m in c.modules:
                if m.name == module_name:
                    return self.get_au(file, name, type, c=m)
        elif isinstance(c, Module):
            for ub in c.blocks:
                au = self.get_au(file, name, type, c=ub)
                if au is not None:
                    return au
        elif isinstance(c, UnitBlock):
            for au in c.atomic_units:
                if au.type == type and au.name == name:
                    return au
        return None

    def get_associated_au(
        self,
        file: str,
        type: str,
        attribute_name: str,
        pattern: Pattern[str],
        attribute_parents: List[str],
        code: Project | Module | UnitBlock | None = None,
    ) -> Optional[AtomicUnit]:
        code = self.code if code is None else code
        if isinstance(code, Project):
            module_name = os.path.basename(os.path.dirname(file))
            for m in code.modules:
                if m.name == module_name:
                    return self.get_associated_au(
                        file, type, attribute_name, pattern, attribute_parents, code=m
                    )
        elif isinstance(code, Module):
            for ub in code.blocks:
                au = self.get_associated_au(
                    file, type, attribute_name, pattern, attribute_parents, code=ub
                )
                if au is not None:
                    return au
        elif isinstance(code, UnitBlock):
            for au in code.atomic_units:
                if au.type == type and self.check_required_attribute(
                    au.attributes, attribute_parents, attribute_name, None, pattern
                ):
                    return au
        return None

    def get_attributes_with_name_and_value(
        self,
        attributes: List[KeyValue] | List[Attribute],
        parents: List[str],
        name: str,
        value: Optional[Any] = None,
        pattern: Optional[Pattern[str]] = None,
    ) -> List[KeyValue]:
        aux: List[KeyValue] = []
        for a in attributes:
            if a.name.split("dynamic.")[-1] == name and parents == [""]:
                if (
                    value and isinstance(a.value, str) and a.value.lower() == value
                ) or (
                    pattern
                    and isinstance(a.value, str)
                    and re.match(pattern, a.value.lower())
                ):
                    aux.append(a)
                elif (
                    value and isinstance(a.value, str) and a.value.lower() != value
                ) or (
                    pattern
                    and isinstance(a.value, str)
                    and not re.match(pattern, a.value.lower())
                ):
                    continue
                elif not value and not pattern:
                    aux.append(a)
            elif a.name.split("dynamic.")[-1] in parents:
                aux += self.get_attributes_with_name_and_value(
                    a.keyvalues, [""], name, value, pattern
                )
            elif a.keyvalues != []:
                aux += self.get_attributes_with_name_and_value(
                    a.keyvalues, parents, name, value, pattern
                )
        return aux

    def check_required_attribute(
        self,
        attributes: List[Attribute] | List[KeyValue],
        parents: List[str],
        name: str,
        value: Optional[Any] = None,
        pattern: Optional[Pattern[str]] = None,
        return_all: bool = False,
    ) -> Union[Optional[KeyValue], List[KeyValue]]:
        attributes = self.get_attributes_with_name_and_value(
            attributes, parents, name, value, pattern
        )
        if attributes != []:
            if return_all:
                return attributes  # type: ignore
            return attributes[0]

        return None

    def check_database_flags(
        self,
        au: AtomicUnit,
        file: str,
        smell: str,
        flag_name: str,
        safe_value: str,
        required_flag: bool = True,
    ) -> List[Error]:
        database_flags = self.get_attributes_with_name_and_value(
            au.attributes, ["settings"], "database_flags"
        )
        found_flag = False
        errors: List[Error] = []
        if database_flags != []:
            for flag in database_flags:
                name = self.check_required_attribute(
                    flag.keyvalues, [""], "name", flag_name
                )
                if name is not None:
                    found_flag = True
                    value = self.check_required_attribute(flag.keyvalues, [""], "value")
                    if (
                        isinstance(value, KeyValue)
                        and isinstance(value.value, str)
                        and value.value.lower() != safe_value
                    ):
                        errors.append(Error(smell, value, file, repr(value)))
                        break
                    elif not value and required_flag:
                        errors.append(
                            Error(
                                smell,
                                flag,
                                file,
                                repr(flag),
                                f"Suggestion: check for a required attribute with name 'value'.",
                            )
                        )
                        break
        if not found_flag and required_flag:
            errors.append(
                Error(
                    smell,
                    au,
                    file,
                    repr(au),
                    f"Suggestion: check for a required flag '{flag_name}'.",
                )
            )
        return errors

    def iterate_required_attributes(
        self,
        attributes: List[KeyValue] | List[Attribute],
        name: str,
        check: Callable[[KeyValue], bool],
    ):
        i = 0
        attribute = self.check_required_attribute(attributes, [""], f"{name}[{i}]")

        while isinstance(attribute, KeyValue):
            if check(attribute):
                return True, attribute
            i += 1
            attribute = self.check_required_attribute(attributes, [""], f"{name}[{i}]")

        return False, None

    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        return []

    def __check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        errors: List[Error] = []
        errors += self._check_attribute(attribute, atomic_unit, parent_name, file)
        for attr_child in attribute.keyvalues:
            errors += self.__check_attribute(
                attr_child, atomic_unit, attribute.name, file
            )
        return errors

    def _check_attributes(self, atomic_unit: AtomicUnit, file: str) -> List[Error]:
        errors: List[Error] = []
        for attribute in atomic_unit.attributes:
            errors += self.__check_attribute(attribute, atomic_unit, "", file)
        return errors
