import json
import os

from typing import Tuple, List
from glitch.rego.go.wrapper import run_rego
from glitch.repr.inter import *
from glitch.analysis.rules import Error


def run_analyses(
    input: str, 
    config: str,
    smell_types: Tuple[str, ...],
    regopy: bool = True
) -> List[Error]:
    input_data = json.loads(input)

    data: dict[str, str] = {}
    if config and os.path.exists(config):
        with open(config) as f:
            data = json.load(f)

    rego_modules = load_rego_modules_from_folder("./glitch/rego/queries/security")

    result = run_rego(input_data, data, rego_modules)

    if "error" in result:
        print("Error:", result["error"])
        return set()

    errors: List[Error] = []
    
    # Parse the Go Rego engine output to a set of errors
    for entry in result:
        expressions = entry.get("expressions", [])
        for expr in expressions:
            values_list = expr.get("value", [])
            for values in values_list:        # values is itself a list
                for val in values:            # now val is the dict with 'element', 'path', etc.
                    if isinstance(val, dict) and "element" in val:
                        element = element_from_dict(val["element"])
                        error = Error(
                            code=val.get("type", ""),
                            el=element,
                            path=val.get("path", ""),
                            repr=repr(element),
                            opt_msg=val.get("description")
                        )
                        errors.append(error)
    return errors


def load_rego_modules_from_folder(folder_path: str) -> dict[str, str]:
    modules = {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.rego'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as f:
                modules[filename] = f.read()
    return modules # type: ignore

def element_from_dict(data: dict) -> CodeElement:
    """
    Recursively builds a CodeElement from a dict like the Rego query output.
    """
    # Step 1: Extract common element info
    info = ElementInfo(
        line=data.get("line", -1),
        column=data.get("column", -1),
        end_line=data.get("end_line", -1),
        end_column=data.get("end_column", -1),
        code=data.get("code", ""),
    )

    ir_type = data.get("ir_type")

    # Step 2: Handle by type
    if ir_type == "String":
        return String(data["value"], info)

    elif ir_type == "Integer":
        return Integer(data["value"], info)

    elif ir_type == "Float":
        return Float(data["value"], info)

    elif ir_type == "Boolean":
        return Boolean(data["value"], info)
    
    elif ir_type == "Complex":
        return Complex(data["value"], info)

    elif ir_type == "Null":
        return Null(info)

    elif ir_type == "Array":
        values = [element_from_dict(v) for v in data["value"]]
        return Array(values, info)

    elif ir_type == "Hash":
        # Hash is stored as dict[Expr, Expr]
        value = {}
        for pair in data["value"]:
            key = element_from_dict(pair["key"])
            val = element_from_dict(pair["value"])
            value[key] = val
        return Hash(value, info)

    elif ir_type == "VariableReference":
        return VariableReference(data["value"], info)

    elif ir_type == "Attribute":
        value = element_from_dict(data["value"])
        return Attribute(data["name"], value, info)

    elif ir_type == "Variable":
        value = element_from_dict(data["value"])
        return Variable(data["name"], value, info)

    elif ir_type == "KeyValue":
        value = element_from_dict(data["value"])
        return KeyValue(data["name"], value, info)

    # Expressions and binary/unary operations
    elif ir_type in {
        "Or", "And", "Sum", "Equal", "NotEqual", "LessThan",
        "LessThanOrEqual", "GreaterThan", "GreaterThanOrEqual",
        "In", "Subtract", "Multiply", "Divide", "Modulo",
        "Power", "RightShift", "LeftShift", "Access",
        "BitwiseAnd", "BitwiseOr", "BitwiseXor", "Assign",
    }:
        left = element_from_dict(data["left"])
        right = element_from_dict(data["right"])
        cls = globals()[ir_type]  # lookup class by name
        return cls(info, left, right)

    elif ir_type in {"Not", "Minus"}:
        expr = element_from_dict(data["expr"])
        cls = globals()[ir_type]
        return cls(info, expr)

    elif ir_type == "FunctionCall":
        args = [element_from_dict(a) for a in data["args"]]
        return FunctionCall(data["name"], args, info)

    elif ir_type == "MethodCall":
        receiver = element_from_dict(data["receiver"])
        args = [element_from_dict(a) for a in data["args"]]
        return MethodCall(receiver, data["method"], args, info)

    elif ir_type == "Comment":
        # Dont know if Info is needed
        return Comment(data.get("content", ""))
    
    elif ir_type == "ConditionalStatement":
        condition = element_from_dict(data["condition"])
        cond_type = getattr(ConditionalStatement.ConditionType, data["type"])
        cond = ConditionalStatement(condition, cond_type, data.get("is_default", False))
        if data.get("else_statement"):
            cond.else_statement = element_from_dict(data["else_statement"])
        # Inherits from Block, which can have a list of statements
        for s in data.get("statements", []):
            cond.add_statement(element_from_dict(s))
        return cond

    elif ir_type == "Block":
        blk = Block()
        blk.set_element_info(info)
        for s in data.get("statements", []):
            blk.add_statement(element_from_dict(s))
        return blk

    elif ir_type == "AtomicUnit":
        name = element_from_dict(data["name"])
        unit = AtomicUnit(name, data.get("type", "unknown"))
        for attr in data.get("attributes", []):
            unit.add_attribute(element_from_dict(attr))
        return unit

    elif ir_type == "UnitBlock":
        unit = UnitBlock(data.get("name"), data.get("type", "unknown"))
        for attr in data.get("attributes", []):
            unit.add_attribute(element_from_dict(attr))
        for c in data.get("comments", []):
            unit.add_comment(element_from_dict(c))
        for v in data.get("variables", []):
            unit.add_variable(element_from_dict(v))
        for au in data.get("atomic_units", []):
            unit.add_atomic_unit(element_from_dict(au))
        for ub in data.get("unit_blocks", []):
            unit.add_unit_block(element_from_dict(ub))
        for d in data.get("dependencies", []):
            unit.add_dependency(element_from_dict(d))
        unit.path = data.get("path", "")
        return unit
    
    elif ir_type == "Dependency":
        # Dont know if Info is needed
        return Dependency(data.get("names", []))
    
    else:
        # Unknown type: treat as generic CodeElement
        return CodeElement(info)
