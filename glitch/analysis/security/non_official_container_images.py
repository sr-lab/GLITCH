from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import CodeElement, KeyValue, Hash, String
from glitch.analysis.utils import parse_container_image_name
from typing import List


class NonOfficialContainerImage(SecuritySmellChecker):
    # NOTE: This is the implementation for Nomad and Swarm
    def check(self, element: CodeElement, file: str) -> List[Error]:
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

        img_name, _, _ = parse_container_image_name(image)

        if img_name != "":
            for off_img in SecurityVisitor.DOCKER_OFFICIAL_IMAGES:
                off_img_dockerio = f"docker.io/library/{off_img}"
                off_img_library = f"library/{off_img}"
                off_img_complete_link = f"registry.hub.docker.com/library/{off_img}"

                if (
                    img_name == off_img
                    or img_name == off_img_dockerio
                    or img_name == off_img_library
                    or img_name == off_img_complete_link
                ):
                    return []

            return [
                Error("sec_non_official_image", bad_element, file, repr(bad_element))
            ]

        return []
