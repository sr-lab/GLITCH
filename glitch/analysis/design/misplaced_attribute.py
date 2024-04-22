from typing import List, Optional
from glitch.analysis.rules import Error
from glitch.analysis.design.smell_checker import DesignSmellChecker
from glitch.tech import Tech
from glitch.repr.inter import *


class ChefMisplacedAttribute(DesignSmellChecker):
    @staticmethod
    def tech() -> Optional[Tech]:
        return Tech.chef

    def check(self, element: CodeElement, file: str) -> List[Error]:
        if isinstance(element, AtomicUnit):
            order: List[int] = []
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
                return [
                    Error("design_misplaced_attribute", element, file, repr(element))
                ]
        return []


class PuppetMisplacedAttribute(DesignSmellChecker):
    @staticmethod
    def tech() -> Optional[Tech]:
        return Tech.puppet

    def check(self, element: CodeElement, file: str) -> List[Error]:
        if isinstance(element, AtomicUnit):
            for i, attr in enumerate(element.attributes):
                if attr.name == "ensure" and i != 0:
                    return [
                        Error(
                            "design_misplaced_attribute",
                            element,
                            file,
                            repr(element),
                        )
                    ]
        elif isinstance(element, UnitBlock):
            optional = False
            for attr in element.attributes:
                if attr.value is not None:
                    optional = True
                elif optional:
                    return [
                        Error(
                            "design_misplaced_attribute",
                            element,
                            file,
                            repr(element),
                        )
                    ]
        return []
