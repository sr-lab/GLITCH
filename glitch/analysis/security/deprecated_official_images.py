from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import CodeElement, KeyValue, Hash, String
from typing import List


class DeprecatedOfficialDockerImages(SecuritySmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        image = ""
        bad_element = element
        if isinstance(element, KeyValue) and element.name == "image":
            if isinstance(element.value, String):
                image = element.value.value
        elif (
            isinstance(element, KeyValue)
            and element.name == "config"
            and isinstance(element.value, Hash)
        ):
            for k, v in element.value.value.items():
                if isinstance(k, String) and k.value == "image":
                    image = v.value
                    bad_element = v
                    break
        if image != "":
            img_name, _, _ = SecurityVisitor.image_parser(image)
            for obsolete_img in SecurityVisitor.DEPRECATED_OFFICIAL_DOCKER_IMAGES:
                if img_name == obsolete_img:
                    errors.append(
                        Error("sec_depr_off_imgs", bad_element, file, repr(bad_element))
                    )
                    break

        return errors
