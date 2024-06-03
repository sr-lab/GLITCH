from glitch.tech import Tech
from glitch.repr.inter import *


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
            case "directory", Tech.chef:
                return "file"
            case "ansible.builtin.file", Tech.ansible:
                return "file"
            case "ansible.builtin.user", Tech.ansible:
                return "user"
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
        au_type = NamesDatabase.get_au_type(au_type, tech)
        match name, au_type, tech:
            case "path", "file", Tech.puppet | Tech.chef | Tech.ansible:
                return "path"
            case "owner", "file", Tech.puppet | Tech.chef | Tech.ansible:
                return "owner"
            case "mode", "file", Tech.puppet | Tech.chef | Tech.ansible:
                return "mode"
            case "content", "file", Tech.puppet | Tech.chef | Tech.ansible:
                return "content"
            case "state", "file", Tech.chef:
                return "action"
            case "state", "file", Tech.ansible:
                return "state"
            case "state", "file" | "user", Tech.puppet:
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
            case "present", "state", "user", Tech.puppet:
                return "present"
            case "present", "state", "file" | "user", Tech.chef:
                return ":create"
            case "absent", "state", "file" | "user", Tech.chef:
                return ":delete"
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
            case "ensure", "file" | "user", Tech.puppet:
                return "state"
            case "state", "file" | "user", Tech.ansible:
                return "state"
            case "action", "file" | "user", Tech.chef:
                return "state"
            case _:
                pass

        return name

    @staticmethod
    def get_attr_value(value: Expr, name: str, au_type: str, tech: Tech) -> Expr:
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
        v = None
        if isinstance(value, (VariableReference, String)):
            v = value.value

        if v is not None:
            match v, name, au_type, tech:
                case "present" | "directory" | "absent", "state", "file", Tech.puppet:
                    pass
                case "file", "state", "file", Tech.puppet | Tech.ansible:
                    v = "present"
                case "touch", "state", "file", Tech.ansible:
                    v = "present"
                case ":create", "state", "file" | "user", Tech.chef:
                    v = "present"
                case ":touch", "state", "file", Tech.chef:
                    v = "present"
                case ":delete", "state", "file" | "user", Tech.chef:
                    v = "absent"
                case _:
                    return value

            return String(v, ElementInfo.from_code_element(value))

        return value
