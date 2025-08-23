from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import CodeElement, Hash, String, UnitBlock, UnitBlockType
from typing import List


class MultipleServicesPerDeploymentUnitCheck(SecuritySmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        # FIXME: Besides log collectors, there are other types of agents/sidecars for observability (some of which are also on the log collector list)
        # and proxies which should also be allowed besides the main microservice
        errors: List[Error] = []
        if isinstance(element, UnitBlock) and element.type == UnitBlockType.block:
            main_service_found = False
            for au in element.atomic_units:
                if au.type in ["task.docker", "task.podman"]:
                    image_name = ""
                    for att in au.attributes:
                        if att.name == "config" and isinstance(att.value, Hash):
                            for k, v in att.value.value.items():
                                if isinstance(k, String) and k.value == "image":
                                    image_name, _, _ = SecurityVisitor.image_parser(
                                        v.value
                                    )
                                    break
                            if image_name != "":
                                break

                    if image_name in SecurityVisitor.LOG_AGGREGATORS_AND_COLLECTORS:
                        continue

                    elif main_service_found:
                        errors.append(
                            Error("arc_multiple_services", au, file, repr(au))
                        )
                    else:
                        main_service_found = True
                elif main_service_found:
                    # when there are other types of tasks that aren't docker or podman based
                    # and one that is likely the main microservice has already been found
                    errors.append(Error("arc_multiple_services", au, file, repr(au)))

        return errors
