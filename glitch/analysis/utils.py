from typing import Tuple


def parse_container_image_name(img_name: str) -> Tuple[str, str, str]:
    image, tag, digest = "", "", ""

    if "@" in img_name:
        parts_dig = img_name.split("@")
        digest = parts_dig[-1]
        if ":" in parts_dig[0]:
            parts_tag = parts_dig[0].split(":")
            image = parts_tag[0]
            tag = parts_tag[1]
        else:
            image = parts_dig[0]

    elif ":" in img_name:
        parts_tag = img_name.split(":")
        image = parts_tag[0]
        tag = parts_tag[1]
    else:
        image = img_name

    return image, tag, digest
