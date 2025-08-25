from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.repr.inter import CodeElement, Hash, AtomicUnit, Array, Boolean
from typing import List


class WobblyServiceInteractionCheck(SecuritySmellChecker):
    #FIXME: The class is currently wrongly named should 
    # be missinghealthchecks, although in part it is checking for the WobblyServiceInteraction 
    # in the case of Nomad (See Consul Comment below) so the checks need to be split
    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        
        if isinstance(element, AtomicUnit):
            au = element
            found_healthcheck = False
            has_disable_nomad = False
            
            for att in au.attributes:
                if found_healthcheck:
                    break
                if att.name == "healthcheck":
                    found_healthcheck = True
                    if isinstance(att.value, Hash):
                        for k, v in att.value.value.items():
                            if k.value == "disable" and (
                                v.value or v.value.lower() == "true"
                            ):
                                errors.append(Error("arc_missing_healthchecks", au, file, repr(au)))
                                break
                            elif k.value == "test":
                                if isinstance(v.value, Array):
                                    if (
                                        len(v.value.value) >= 1
                                        and v.value.value[0] == "NONE"
                                    ):
                                        errors.append(
                                            Error("arc_missing_healthchecks", au, file, repr(au))
                                        )
                                        break
                    break
                elif att.name == "config" and isinstance(att.value, Hash):
                    for k, v in att.value.value.items():
                        if k.value == "healthchecks" and isinstance(v, Hash):
                            for _k, _v in v.value.items():
                                if (
                                    _k.value == "disable"
                                    and isinstance(_v, Boolean)
                                    and _v.value
                                ):
                                    has_disable_nomad = True
                                    break
                                elif has_disable_nomad:
                                    break
                        if has_disable_nomad:
                            break

                elif att.name == "service" and isinstance(att.value, Hash):
                    for k, v in att.value.value.items():
                        if k.value == "check" and isinstance(v, Hash):
                            found_healthcheck = True
                            break
                        elif k.value == "connect" and isinstance(v, Hash):
                            for _k, _v in v.value.items():
                                if _k.value == "sidecar_service" and isinstance(
                                    _v, Hash
                                ):
                                    # Checks for use of Consul service mesh, sidecar proxy that
                                    # provides timeouts and circuit breaks that also avoid this smell
                                    # technically the original smell is detectable in Nomad if this is not present
                                    found_healthcheck = True
                                    break
                            if found_healthcheck:
                                break

                    if not found_healthcheck:
                        errors.append(Error("arc_missing_healthchecks", au, file, repr(au)))

                if (
                    att.name in ["config", "service"]
                    and isinstance(att.value, Hash)
                    and not found_healthcheck
                    and has_disable_nomad
                ):
                    errors.append(Error("arc_missing_healthchecks", au, file, repr(au)))
        
            if element.type == "service" and not found_healthcheck:
                errors.append(Error("arc_missing_healthchecks",au,file,repr(au)))

        return errors
