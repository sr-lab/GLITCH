from glitch.tech import Tech
from glitch.repr.inter import *


class TemplateDatabase:
    @staticmethod
    def get_template(code_element: CodeElement, tech: Tech) -> str:
        """Returns the template for the given code element on a given tech.

        Args:
            type (CodeElement): The code element being considered.
            tech (Tech): The tech being considered.

        Returns:
            str: The template.
        """
        if isinstance(code_element, Attribute) and tech == Tech.puppet:
            return "{} => {},\n"
        elif isinstance(code_element, Attribute) and tech == Tech.chef:
            return "{} {}\n"
        elif isinstance(code_element, Attribute) and tech == Tech.ansible:
            return "{}: {}\n"
        elif isinstance(code_element, Attribute) and tech == Tech.terraform:
            return "{} = {}\n"

        raise NotImplementedError(
            "Template not found for the given code element and tech."
        )
