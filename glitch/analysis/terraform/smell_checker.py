import os

from re import Pattern
from typing import Optional, List, Callable
from glitch.repr.inter import *
from glitch.analysis.rules import Error, SmellChecker
from glitch.analysis.expr_checkers.string_checker import StringChecker


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
                    au, attribute_parents, attribute_name, None, pattern
                ):
                    return au
        return None
    
    def get_attributes(
        self,
        element: AtomicUnit | Attribute | UnitBlock,
        parents: List[str],
        name: str,
    ) -> List[Attribute | UnitBlock]:
        res: List[Attribute | UnitBlock] = []
        if isinstance(element, AtomicUnit):
            for attr in element.attributes:
                elems = self.get_attributes(attr, parents, name)
                res.extend(elems)
            for ub in element.statements:
                if isinstance(ub, UnitBlock):
                    elems = self.get_attributes(ub, parents, name)
                    res.extend(elems)
        elif (
            isinstance(element, UnitBlock)
            and element.type == UnitBlockType.block
            and len(parents) > 0
            and element.name == parents[0]
        ):
            for attribute in element.attributes:
                elems = self.get_attributes(attribute, parents[1:], name)
                res.extend(elems)
            for ub in element.statements + element.unit_blocks:
                if isinstance(ub, UnitBlock):
                    elems = self.get_attributes(ub, parents[1:], name)
                    res.extend(elems)
        elif (
            len(parents) == 0
            and element.name == name
        ):
            res.append(element)
        
        return res

    def get_attribute(
        self,
        element: AtomicUnit | Attribute | UnitBlock,
        parents: List[str],
        name: str,
    ) -> Attribute | UnitBlock | None:
        attributes = self.get_attributes(element, parents, name)
        return attributes[0] if len(attributes) > 0 else None

    def check_required_attribute(
        self,
        atomic_unit: AtomicUnit,
        parents: List[str] | List[List[str]],
        name: str,
        value: Optional[str] = None,
        pattern: Optional[Pattern[str]] = None,
    ) -> Optional[Attribute | UnitBlock]:
        element = None
        # In the case we have a list, we consider that one of the 
        # parents list must be satisfied. This is particularly useful
        # when attributes changes its location between Terraform versions.
        has_parents_list = False
        for parents_list in parents:
            if isinstance(parents_list, list):
                has_parents_list = True
                element = self.get_attribute(atomic_unit, parents_list, name)
                if element is not None:
                    break
        if not has_parents_list:
            element = self.get_attribute(atomic_unit, parents, name) # type: ignore
        
        if value is not None:
            if value == "any_not_empty":
                value_checker = StringChecker(lambda x: len(x.strip()) > 0)
            else:
                value_checker = StringChecker(lambda x: x.lower() == value.lower())
            
            if element is not None and isinstance(element, Attribute):
                if (
                    value == "true" 
                    and isinstance(element.value, Boolean) 
                    and element.value.value
                ):
                    return element
                elif (
                    value == "false" 
                    and isinstance(element.value, Boolean) 
                    and not element.value.value
                ):
                    return element
                elif value == "non_empty_list":
                    if isinstance(element.value, Array) and len(element.value.value) > 0:
                        return element
                elif value_checker.check(element.value):
                    return element
                return None
        elif pattern is not None and element is not None and isinstance(element, Attribute):
                # HACK: using the code is sort of an hack (avoids dealing with Access)
                if pattern.match(element.value.code) is not None:
                    return element
                return None
        else:
            return element

    def check_database_flags(
        self,
        au: AtomicUnit,
        file: str,
        smell: str,
        flag_name: str,
        safe_value: str,
        required_flag: bool = True,
    ) -> List[Error]:
        database_flags = self.get_attributes(
            au, ["settings"], "database_flags"
        )
        found_flag = False
        errors: List[Error] = []
        if database_flags != []:
            for flag in database_flags:
                if isinstance(flag, Attribute) or flag.name is None:
                    continue
            
                # Fake AtomicUnit to use the check_required_attribute method
                fake_au = AtomicUnit(Null(), "")
                fake_au.statements = [flag]
                name = self.check_required_attribute(
                    fake_au, [flag.name], "name", flag_name
                )
                # Attribute not found but it is not required
                if name is None and not required_flag:
                    continue

                # Attribute found
                if name is not None:
                    found_flag = True
                    value = self.check_required_attribute(fake_au, [flag.name], "value", value=safe_value)
                    # But value is not correct
                    if value is None:
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
        element: Attribute | UnitBlock,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, Attribute):
            errors += self._check_attribute(element, atomic_unit, parent_name, file)
        elif element.type == UnitBlockType.block:
            for attr in element.attributes:
                errors += self._check_attribute(attr, atomic_unit, element.name, file) # type: ignore
            for statement in element.statements:
                if isinstance(statement, UnitBlock) and statement.type == UnitBlockType.block:
                    errors += self.__check_attribute(statement, atomic_unit, element.name, file) # type: ignore
        return errors

    def _check_attributes(self, element: AtomicUnit, file: str) -> List[Error]:
        errors: List[Error] = []
        for attribute in element.attributes:
            errors += self.__check_attribute(attribute, element, "", file)
        for statement in element.statements:
            if isinstance(statement, UnitBlock) and statement.type == UnitBlockType.block:
                errors += self.__check_attribute(statement, element, "", file)
        return errors
