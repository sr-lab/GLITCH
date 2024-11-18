from glitch.tech import Tech
from glitch.repr.inter import *
from typing import Tuple


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
            case "link", Tech.chef:
                return "file"
            case "ansible.builtin.file", Tech.ansible:
                return "file"
            case "ansible.builtin.user", Tech.ansible:
                return "user"
            case "ansible.builtin.package", Tech.ansible:
                return "package"
            case "ansible.builtin.service", Tech.ansible:
                return "service"
            case "ansible.builtin.yum" | "yum", Tech.ansible:
                return "package"
            case "ansible.builtin.apt" | "apt", Tech.ansible:
                return "package"
            case "amazon.aws.s3_bucket", Tech.ansible:
                return "aws_s3_bucket"
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
            case "state", "file" | "user" | "package" | "service", Tech.chef:
                return "action"
            case "state", "file", Tech.ansible:
                return "state"
            case "state", "file" | "user" | "package" | "service", Tech.puppet:
                return "ensure"
            case "enabled", "service", Tech.puppet:
                return "enable"
            case "enabled", "service", Tech.chef:
                return "action"
            case "name", "aws_s3_bucket", Tech.terraform:
                return "bucket"
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
            case "present", "state", "package", Tech.chef:
                return ":install"
            case "absent", "state", "package", Tech.chef:
                return ":remove"
            case "latest", "state", "package", Tech.chef:
                return ":upgrade"
            case "purged", "state", "package", Tech.chef:
                return ":purge"
            case "nothing", "state", "package", Tech.chef:
                return ":nothing"
            case "reconfig", "state", "package", Tech.chef:
                return ":reconfig"
            case "start", "state", "service", Tech.puppet:
                return "running"
            case "stop", "state", "service", Tech.puppet:
                return "stopped"
            case "start", "state", "service", Tech.chef:
                return ":start"
            case "stop", "state", "service", Tech.chef:
                return ":stop"
            case "start", "state", "service", Tech.ansible:
                return "started"
            case "stop", "state", "service", Tech.ansible:
                return "stopped"
            case "true", "enabled", "service", Tech.chef:
                return ":enable"
            case "false", "enabled", "service", Tech.chef:
                return ":disable"
            case _:
                pass
        return value

    @staticmethod
    def __get_attr_name(name: str, au_type: str, tech: Tech) -> str:
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
            case "ensure", "file" | "user" | "package" | "service", Tech.puppet:
                return "state"
            case "state", "file" | "user" | "package" | "service", Tech.ansible:
                return "state"
            case "action", "file" | "user" | "package" | "service", Tech.chef:
                return "state"
            case "enable", "service", Tech.puppet:
                return "enabled"
            case "bucket", "aws_s3_bucket", Tech.terraform:
                return "name"
            case _:
                pass

        return name

    @staticmethod
    def __get_attr_value(value: Expr, name: str, au_type: str, tech: Tech) -> Expr:
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

        if isinstance(value, Integer) and name == "mode":
            return String(
                oct(value.value).replace('o', ''), 
                ElementInfo.from_code_element(value)
            )

        if v is not None:
            match v, name, au_type, tech:
                case "present" | "directory" | "absent", "state", "file" | "user", Tech.puppet:
                    pass
                case "latest" | "present" | "absent" | "purged" | "disabled", "state", "package", Tech.puppet:
                    pass
                case "installed", "state", "package", Tech.puppet:
                    v = "present"
                case "running" | "true", "state", "service", Tech.puppet:
                    v = "start"
                case "stopped" | "false", "state", "service", Tech.puppet:
                    v = "stop"
                case ":start", "state", "service", Tech.chef:
                    v = "start"
                case ":stop", "state", "service", Tech.chef:
                    v = "stop"
                case "started", "state", "service", Tech.ansible:
                    v = "start"
                case "stopped", "state", "service", Tech.ansible:
                    v = "stop"
                case "file", "state", "file", Tech.puppet | Tech.ansible:
                    v = "present"
                case "touch", "state", "file", Tech.ansible:
                    v = "present"
                case ":create" | ":nothing", "state", "file" | "user", Tech.chef:
                    v = "present"
                case ":touch" | ":nothing" | ":create_if_missing", "state", "file", Tech.chef:
                    v = "present"
                case ":upgrade", "state", "package", Tech.chef:
                    v = "latest"
                case ":purge", "state", "package", Tech.chef:
                    v = "purged"
                case ":reconfig", "state", "package", Tech.chef:
                    v = "reconfig"
                case ":nothing", "state", "package", Tech.chef:
                    v = "nothing"
                case ":delete", "state", "file" | "user", Tech.chef:
                    v = "absent"
                case ":install", "state", "package", Tech.chef:
                    v = "present"
                case ":remove", "state", "package", Tech.chef:
                    v = "absent"
                case ":enable", "enabled", "service", Tech.chef:
                    v = "true"
                case ":disable", "enabled", "service", Tech.chef:
                    v = "false"
                case _:
                    return value

            return String(v, ElementInfo.from_code_element(value))

        return value
    
    @staticmethod
    def get_attr_pair(value: Expr, attr_name: str, au_type: str, tech: Tech) -> Tuple[str, Expr]:
        attr_name = NamesDatabase.__get_attr_name(attr_name, au_type, tech)

        v = None
        if isinstance(value, (VariableReference, String)):
            v = value.value
        if v is not None:
            match v, attr_name, au_type, tech:
                case ":enable", "state", "service", Tech.chef:
                    return (
                        "enabled",
                        String("true", ElementInfo.from_code_element(value)),
                    )
                case ":disable", "state", "service", Tech.chef:
                    return (
                        "enabled", 
                        String("false", ElementInfo.from_code_element(value))
                    )
                case _:
                    pass
        
        return (
            attr_name,
            NamesDatabase.__get_attr_value(value, attr_name, au_type, tech)
        )


class NormalizationVisitor:
    def __init__(self, tech: Tech) -> None:
        self.tech = tech
    
    def visit(self, element: CodeElement) -> None:
        if isinstance(element, AtomicUnit):
            self.visit_atomic_unit(element)
        elif isinstance(element, UnitBlock):
            self.visit_unit_block(element)
        elif isinstance(element, ConditionalStatement):
            self.visit_conditional_statement(element)
        
        if isinstance(element, Block):
            self.visit_block(element)

    def visit_atomic_unit(self, element: AtomicUnit) -> None:
        element.type = NamesDatabase.get_au_type(element.type, self.tech)
        
        # Since Terraform does not define a state, we add it manually
        # FIXME: Probably should be in a better place
        if self.tech == Tech.terraform:
            element.attributes.insert(0, Attribute(
                "state", 
                # The element info should be unique
                String("present", ElementInfo.get_sketched()), 
                ElementInfo.get_sketched()
            ))

        for attr in element.attributes:
            attr.name, attr.value = NamesDatabase.get_attr_pair(
                attr.value, 
                attr.name, 
                element.type, 
                self.tech
            )

    def visit_conditional_statement(self, element: ConditionalStatement) -> None:
        if element.else_statement is not None:
            self.visit(element.else_statement)

    def visit_unit_block(self, element: UnitBlock) -> None:
        for ub in element.unit_blocks:
            self.visit(ub)
        for au in element.atomic_units:
            self.visit(au)

    def visit_block(self, element: Block) -> None:
        for child in element.statements:
            self.visit(child)
        