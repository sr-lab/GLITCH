from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import CodeElement, KeyValue, Hash, String
from glitch.analysis.utils import parse_container_image_name
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
            img_name, _, _ = parse_container_image_name(image)
            for obsolete_img in SecurityVisitor.DEPRECATED_OFFICIAL_DOCKER_IMAGES:
                obsolete_img_dockerio = f"docker.io/library/{obsolete_img}"
                obsolete_img_library = f"library/{obsolete_img}"
                obsolete_img_complete_link = (
                    f"registry.hub.docker.com/library/{obsolete_img}"
                )

                if (
                    img_name == obsolete_img
                    or img_name == obsolete_img_dockerio
                    or img_name == obsolete_img_library
                    or img_name == obsolete_img_complete_link
                ):
                    errors.append(
                        Error("sec_depr_off_imgs", bad_element, file, repr(bad_element))
                    )
                    break

        return errors
