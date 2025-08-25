from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import CodeElement, KeyValue, Hash, String
from glitch.analysis.utils import parse_container_image_name
from typing import List


class ContainerImageTagsSmells(SecuritySmellChecker):
    # NOTE: This is the implementation for Nomad and Swarm
    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        bad_element = element
        if isinstance(element, KeyValue) and (
            (element.name == "image" and isinstance(element.value, String))
            or (isinstance(element.value, Hash) and element.name == "config")
        ):
            image = ""

            if isinstance(element.value, String):
                image = element.value.value
            else:
                for k, v in element.value.value.items():
                    if isinstance(k, String) and k.value == "image":
                        image = v.value
                        bad_element = v
                        break

            has_digest, has_tag = False, False
            _, tag, digest = parse_container_image_name(image)

            if tag != "":
                has_tag = True
            if digest != "":
                has_digest = True

            if image != "" and has_digest:  # image tagged with digest
                checksum_s = digest.split(":")
                checksum = checksum_s[-1]
                if (
                    checksum_s[0] == "sha256" and len(checksum) != 64
                ):  # sha256 256 digest -> 64 hexadecimal digits
                    errors.append(
                        Error(
                            "sec_image_integrity",
                            bad_element,
                            file,
                            repr(bad_element),
                        )
                    )

            if image != "" and has_tag:
                tag = tag.lower()
                if not has_digest:
                    errors.append(
                        Error(
                            "sec_image_integrity",
                            bad_element,
                            file,
                            repr(bad_element),
                        )
                    )

                dangerous_tags: List[str] = SecurityVisitor.DANGEROUS_IMAGE_TAGS

                for dt in dangerous_tags:
                    if dt in tag:
                        errors.append(
                            Error(
                                "sec_unstable_tag",
                                bad_element,
                                file,
                                repr(bad_element),
                            )
                        )
                        break
            if (
                image != "" and not has_digest and not has_tag
            ):  # Image not tagged, avoids mistakenely nomad tasks without images (non-docker or non-podman)
                errors.append(
                    Error("sec_no_image_tag", bad_element, file, repr(bad_element))
                )

        return errors
