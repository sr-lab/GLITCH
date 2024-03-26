from glitch.tech import Tech
from typing import Optional


class NamesDatabase:
    @staticmethod
    def get_au_type(type: str, tech: Tech) -> str:
        """Returns the generic type of the atomic unit with the given type and tech.

        Args:
            type (str): The type of the atomic unit.
            tech (Tech): The tech being considered.

        Returns:
            str: The generic type of the atomic unit.
        """
        match type, tech:
            case "file", Tech.puppet | Tech.chef | Tech.ansible:
                return "file"
            case "ansible.builtin.file", Tech.ansible:
                return "file"
            case _:
                pass
        return type

    @staticmethod
    def reverse_attr_name(name: str, au_type: str, tech: Tech) -> str:
        """Returns the technology-specific name of the attribute with the given name, atomic unit type and tech.

        Args:
            name (str): The name of the attribute.
            au_type (str): The type of the atomic unit.
            tech (Tech): The tech being considered.

        Returns:
            str: The technology-specific name of the attribute.
        """
        match name, au_type, tech:
            case "path", "file", Tech.puppet | Tech.chef | Tech.ansible:
                return "path"
            case "owner", "file", Tech.puppet | Tech.chef | Tech.ansible:
                return "owner"
            case "mode", "file", Tech.puppet | Tech.chef | Tech.ansible:
                return "mode"
            case "content", "file", Tech.puppet | Tech.chef | Tech.ansible:
                return "content"
            case "state", "file", Tech.ansible:
                return "state"
            case "state", "file", Tech.puppet:
                return "ensure"
            case _:
                pass
        return name

    @staticmethod
    def reverse_attr_value(value: str, attr_name: str, au_type: str, tech: Tech) -> str:
        """Returns the technology-specific value of the attribute with the given value, attribute name, atomic unit type and tech.

        Args:
            value (str): The value of the attribute.
            attr_name (str): The name of the attribute.
            au_type (str): The type of the atomic unit.
            tech (Tech): The tech being considered.

        Returns:
            str: The technology-specific value of the attribute.
        """
        match value, attr_name, au_type, tech:
            case "present", "state", "file", Tech.ansible:
                return "file"
            case _:
                pass
        return value

    @staticmethod
    def get_attr_name(name: str, au_type: str, tech: Tech) -> str:
        """Returns the generic name of the attribute with the given name, atomic unit type and tech.

        Args:
            name (str): The name of the attribute.
            au_type (str): The type of the atomic unit.
            tech (Tech): The tech being considered.

        Returns:
            str: The generic name of the attribute.
        """
        match name, au_type, tech:
            case "path", "file", Tech.puppet | Tech.chef | Tech.ansible:
                return "path"
            case "dest", "file", Tech.ansible:
                return "path"
            case "owner", "file", Tech.puppet | Tech.chef | Tech.ansible:
                return "owner"
            case "mode", "file", Tech.puppet | Tech.chef | Tech.ansible:
                return "mode"
            case "content", "file", Tech.puppet | Tech.chef | Tech.ansible:
                return "content"
            case "ensure", "file", Tech.puppet:
                return "state"
            case "state", "file", Tech.ansible:
                return "state"
            case _:
                pass

        return name

    @staticmethod
    def get_attr_value(
        value: str, name: str, au_type: str, tech: Tech
    ) -> Optional[str]:
        """Returns the generic value of the attribute with the given value, name,
        atomic unit type and tech.

        Args:
            value (str): The value of the attribute.
            name (str): The name of the attribute.
            au_type (str): The type of the atomic unit.
            tech (Tech): The tech being considered.

        Returns:
            str: The generic value of the attribute.
        """
        match value, name, au_type, tech:
            case "file", "state", "file", Tech.puppet | Tech.ansible:
                return "present"
            case "touch", "state", "file", Tech.ansible:
                return "present"
            case _:
                pass

        return value
