from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import CodeElement, Hash, String, UnitBlock
from glitch.analysis.utils import parse_container_image_name
from typing import List


class LogAggregatorAbsence(SecuritySmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []

        if isinstance(element, UnitBlock):
            # HACK: Besides the ones we are explicitly stating a registry we assume the default, normally Docker hub
            log_collectors: List[str] = SecurityVisitor.LOG_AGGREGATORS_AND_COLLECTORS

            log_drivers: List[str] = SecurityVisitor.DOCKER_LOG_DRIVERS

            has_log_collector = False

            for au in element.atomic_units:
                if au.type != "service" and not au.type.startswith("task."):
                    # Don't analyze Unit Blocks which aren't tasks or services
                    return []

                for att in au.attributes:
                    image = ""
                    if att.name == "config" and isinstance(att.value, Hash):
                        for k, v in att.value.value.items():
                            if isinstance(k, String) and k.value == "image":
                                image = v.value
                                break

                    elif att.name == "image" and isinstance(att.value, String):
                        image = att.value.value

                    img_name, _, _ = parse_container_image_name(image)

                    if image != "":
                        for lc in log_collectors:
                            if img_name.startswith(lc):
                                return []
                        break

            # if it doesn't have a log collector/aggregator in the deployment
            if not has_log_collector:
                for au in element.atomic_units:
                    has_logging = False
                    for att in au.attributes:
                        if has_logging:
                            break
                        if att.name == "logging" and isinstance(att.value, Hash):
                            for k, v in att.value.value.items():
                                if (
                                    k.value == "driver"
                                    and isinstance(v, String)
                                    and v.value in log_drivers
                                ):
                                    has_logging = True
                                    break
                        elif att.name == "config" and isinstance(att.value, Hash):
                            for k, v in att.value.value.items():
                                if (
                                    isinstance(k, String)
                                    and k.value == "logging"
                                    and isinstance(v, Hash)
                                ):
                                    for _k, _v in v.value.items():
                                        if (
                                            _k.value == "driver"
                                            and isinstance(_v, String)
                                            and _v.value in log_drivers
                                        ):
                                            has_logging = True
                                            break
                                if has_logging:
                                    break

                    if not has_logging:
                        errors.append(Error("arc_no_logging", au, file, repr(au)))

        return errors
