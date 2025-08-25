from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.repr.inter import CodeElement, KeyValue, Boolean, Hash, String
from typing import List


class PrivilegedContainerUse(SecuritySmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        if isinstance(element, KeyValue):

            if (
                element.name == "privileged"
                and isinstance(element.value, Boolean)
                and element.value.value
            ):
                return [Error("sec_privileged_containers", element, file, repr(element))]
            elif element.name == "config" and isinstance(element.value, Hash):
                for k, v in element.value.value.items():
                    if isinstance(k, String) and k.value == "privileged" and v.value:
                        return [Error("sec_privileged_containers", k, file, repr(k))]

        return []
