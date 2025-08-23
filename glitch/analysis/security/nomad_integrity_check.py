from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.repr.inter import CodeElement, KeyValue, Hash, String
from typing import List


class NomadNoIntegrityCheck(SecuritySmellChecker):
    # FIXME Nomad integrity check (its split from the other integrity checks)
    def check(self, element: CodeElement, file: str) -> List[Error]:
        if isinstance(element, KeyValue):
            if element.name == "artifact" and isinstance(element.value, Hash):
                # Nomad integrity check
                found_checksum = False
                for k, v in element.value.value.items():
                    if (
                        isinstance(k, String)
                        and k.value == "options"
                        and isinstance(v, Hash)
                    ):
                        for _k, _ in v.value.items():
                            if isinstance(_k, String) and _k.value == "checksum":
                                found_checksum = True
                                break
                        if not found_checksum:
                            return [
                                Error(  # type: ignore
                                    "sec_no_int_check", element, file, repr(element)
                                )
                            ]  # type: ignore

                if not found_checksum:
                    return [
                        Error(  # type: ignore
                            "sec_no_int_check", element, file, repr(element)
                        )
                    ]  # type: ignore
        return []
