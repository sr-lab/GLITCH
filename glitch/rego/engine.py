import json
import os

from typing import Tuple, List, Dict, Any, Optional
from glitch.rego.rego_python.src.rego_python import run_rego
from glitch.repr.inter import *
from glitch.analysis.rules import Error


def run_analyses(
    input: str, 
    config: str,
    rego_modules: Dict[str, str],
) -> List[Error]:
    input_data = json.loads(input)

    data: Dict[str, Any] = {}
    if config and os.path.exists(config):
        with open(config) as f:
            data = json.load(f)
    
    if not rego_modules:
        # No modules to run, return empty errors
        return []
    
    result = run_rego(input_data, data, rego_modules)

    if result is None:
        # Nothing to process
        return []

    if isinstance(result, dict) and "error" in result:
        print("Error:", result["error"]) # type: ignore
        return []

    errors: List[Error] = []
    
    flat_values: List[Dict[str, Any]] = []

    # Parse the Go Rego engine output to a set of errors
    # It can be a list or a list of lists, so we put everything in a single list
    for entry in result:
        for expr in entry.get("expressions", []):
            values_list = expr.get("value", [])
            # Normalize nested structure to flat list of dicts
            for item in values_list:
                if isinstance(item, list):
                    flat_values.extend(item) # type: ignore
                elif isinstance(item, dict):
                    flat_values.append(item) # type: ignore
    
    # Create the rego errors
    for val in flat_values:
        if "element" in val:
            element = element_from_dict(val["element"])
            errors.append(Error(
                code=val.get("type", ""),
                el=element,
                path=val.get("path", ""),
                repr=repr(element),
                opt_msg=val.get("description")
            ))
            
    return errors


def load_rego_from_path(file_path: str, result: dict[str, str]) -> None:
    key: str = os.path.split(file_path)[-1]
    with open(file_path, 'r') as f:
        result[key] = f.read()

def element_from_dict(data: Dict[str, Any]) -> CodeElement:
    """
    Recursively builds a CodeElement from a dict like the Rego query output.
    """
    
    # In case we just return a key-value pair from an Hash
    if "key" in data and "value" in data and "ir_type" not in data:
        key_elem = element_from_dict(data["key"])
        value_elem = element_from_dict(data["value"])

        assert isinstance(value_elem, Expr), f"Value in Key Value Hash mapping {value_elem.__class__.__name__} is not an Expr"
        
        # Derive position info from key and value, combining their code
        info = ElementInfo(
            line=getattr(key_elem, "line", -1),
            column=getattr(key_elem, "column", -1),
            end_line=getattr(value_elem, "end_line", -1),
            end_column=getattr(value_elem, "end_column", -1),
            code=f"{key_elem.code}: {value_elem.code}",  # Combined code
        )

        # Extract the name from the key
        if isinstance(key_elem, String):
            name = key_elem.value
        else:
            name = getattr(key_elem, "value", None)
            if isinstance(name, str):
                pass
            else:
                name = str(getattr(key_elem, "code", key_elem))
        
        return KeyValue(name, value_elem, info)
    
    # Step 1: Extract common element info
    info = ElementInfo(
        line=data.get("line", -1),
        column=data.get("column", -1),
        end_line=data.get("end_line", -1),
        end_column=data.get("end_column", -1),
        code=data.get("code", ""),
    )

    ir_type: Optional[str] = data.get("ir_type")

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
    
    elif ir_type == "Undef":
        return Undef(info)

    elif ir_type == "Array":
        values_data = data.get("value", [])
        values: List[Expr] = []
        for v in values_data:
            elem = element_from_dict(v)
            assert isinstance(elem, Expr), f"Element in Array {elem.__class__.__name__} is not an Expr"
            values.append(elem)
        return Array(values, info)

    elif ir_type == "Hash":
        # Hash is stored as dict[Expr, Expr]
        hash_value: Dict[Expr, Expr] = {}
        for pair in data["value"]:
            key = element_from_dict(pair["key"])
            val = element_from_dict(pair["value"])
            assert isinstance(key, Expr), f"Key in Hash Mapping {key.__class__.__name__} is not an Expr"
            assert isinstance(val, Expr), f"Value in Hash Mapping {val.__class__.__name__} is not an Expr"
            hash_value[key] = val
        return Hash(hash_value, info)

    elif ir_type == "VariableReference":
        return VariableReference(data["value"], info)

    elif ir_type == "Attribute":
        value_elem = element_from_dict(data["value"])
        assert isinstance(value_elem, Expr), f"value in Attribute {value_elem.__class__.__name__} is not an Expr"
        return Attribute(data["name"], value_elem, info)

    elif ir_type == "Variable":
        value_elem = element_from_dict(data["value"])
        assert isinstance(value_elem, Expr), f"value in Variable {value_elem.__class__.__name__} is not an Expr"
        return Variable(data["name"], value_elem, info)

    elif ir_type == "KeyValue":
        value_elem = element_from_dict(data["value"])
        assert isinstance(value_elem, Expr), f"value in KeyValue {value_elem.__class__.__name__} is not an Expr"
        return KeyValue(data["name"], value_elem, info)

    # Expressions and binary/unary operations
    elif ir_type in {
        "Or", "And", "Sum", "Equal", "NotEqual", "LessThan",
        "LessThanOrEqual", "GreaterThan", "GreaterThanOrEqual",
        "In", "Subtract", "Multiply", "Divide", "Modulo",
        "Power", "RightShift", "LeftShift", "Access",
        "BitwiseAnd", "BitwiseOr", "BitwiseXor", "Assign",
    }:        
        left_elem = element_from_dict(data["left"])
        right_elem = element_from_dict(data["right"])
        
        if ir_type == "Equal" and left_elem.__class__.__name__ == "CodeElement":
            print("left: ",data["left"])
        
        if ir_type == "Equal" and right_elem.__class__.__name__ == "CodeElement":
            print("right: ", data["right"])
        
        assert isinstance(left_elem, Expr), f"left_elem in BinaryOperation {ir_type}, {left_elem.__class__.__name__} is not an Expr"
        assert isinstance(right_elem, Expr), f"right_elem in BinaryOperation {ir_type}, {right_elem.__class__.__name__} is not an Expr"
        
        binary_op_classes = {
            "Or": Or, "And": And, "Sum": Sum, "Equal": Equal, "NotEqual": NotEqual,
            "LessThan": LessThan, "LessThanOrEqual": LessThanOrEqual,
            "GreaterThan": GreaterThan, "GreaterThanOrEqual": GreaterThanOrEqual,
            "In": In, "Subtract": Subtract, "Multiply": Multiply, "Divide": Divide,
            "Modulo": Modulo, "Power": Power, "RightShift": RightShift,
            "LeftShift": LeftShift, "Access": Access, "BitwiseAnd": BitwiseAnd,
            "BitwiseOr": BitwiseOr, "BitwiseXor": BitwiseXor, "Assign": Assign,
        }
        cls = binary_op_classes[ir_type]
        return cls(info, left_elem, right_elem)

    elif ir_type in {"Not", "Minus"}:
        expr_elem = element_from_dict(data["expr"])
        
        assert isinstance(expr_elem, Expr), f"expr_elem in UnaryRelation {ir_type}, {expr_elem.__class__.__name__} is not an Expr"
        
        unary_op_classes = {"Not": Not, "Minus": Minus}
        cls = unary_op_classes[ir_type]
        return cls(info, expr_elem)

    elif ir_type == "FunctionCall":
        name = data.get("name", "<unknown>")
        args_data = data.get("args", [])
        args: List[Expr] = []
        for a in args_data:
            arg_elem = element_from_dict(a)
            assert isinstance(arg_elem, Expr), f"arg_elem in FunctionCall {arg_elem.__class__.__name__} is not an Expr"
        return FunctionCall(name, args, info)

    elif ir_type == "MethodCall":
        receiver_elem = element_from_dict(data["receiver"])
        assert isinstance(receiver_elem, Expr), f"receiver_elem in MethodCall {receiver_elem.__class__.__name__} is not an Expr"
        
        args_data = data.get("args", [])
        args: List[Expr] = []
        for a in args_data:
            arg_elem = element_from_dict(a)
            assert isinstance(arg_elem, Expr), f"arg_elem in MethodCall {arg_elem.__class__.__name__} is not an Expr"
        return MethodCall(receiver_elem, data["method"], args, info)
        
    elif ir_type == "BlockExpr":
        block = BlockExpr(info)
        for s in data.get("statements", []):
            stmt_elem = element_from_dict(s)
            block.add_statement(stmt_elem)
        return block
    
    elif ir_type == "AddArgs":
        value = data.get("value", [])
        args: List[Expr] = []
        for v in value:
            arg_elem = element_from_dict(v)
            assert isinstance(arg_elem, Expr), f"arg_elem in AddArgs {arg_elem.__class__.__name__} is not an Expr"
            args.append(arg_elem)
        return AddArgs(args, info)

    elif ir_type == "Comment":
        return Comment(data.get("content", ""), info)
    
    elif ir_type == "ConditionalStatement":
        condition = element_from_dict(data["condition"])
        assert isinstance(condition, Expr), f"condition in ConditionalStatement {condition.__class__.__name__} is not an Expr"
        cond_type = getattr(ConditionalStatement.ConditionType, data["type"])
        cond = ConditionalStatement(condition, cond_type, data.get("is_default", False), data.get("is_top", False), info)
        
        else_stmt_data = data.get("else_statement")
        if else_stmt_data:
            else_elem = element_from_dict(else_stmt_data)
            assert isinstance(else_elem, ConditionalStatement), f"else_elem in ConditionalStatement {else_elem.__class__.__name__} is not an ConditionalStatement"
            cond.else_statement = else_elem
            
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
        assert isinstance(name, Expr), f"name in AtomicUnit {name.__class__.__name__} is not an Expr"
        unit = AtomicUnit(name, data.get("type", "unknown"))
        unit.set_element_info(info)
        for attr in data.get("attributes", []):
            attr_elem = element_from_dict(attr)
            assert isinstance(attr_elem, Attribute), f"attr_elem in AtomicUnit {attr_elem.__class__.__name__} is not an Attribute"
            unit.add_attribute(attr_elem)
        return unit

    elif ir_type == "UnitBlock":
        unit = UnitBlock(data.get("name", ""), data.get("type", "unknown"))            
        for attr_data in data.get("attributes", []):
            attr_elem = element_from_dict(attr_data)
            assert isinstance(attr_elem, Attribute), f"attr_elem in UnitBlock {attr_elem.__class__.__name__} is not an Attribute"
            unit.add_attribute(attr_elem)
    
        for comment_data in data.get("comments", []):
            comment_elem = element_from_dict(comment_data)
            assert isinstance(comment_elem, Comment), f"comment_elem in UnitBlock {comment_elem.__class__.__name__} is not an Comment"
            unit.add_comment(comment_elem)
        
        for var_data in data.get("variables", []):
            var_elem = element_from_dict(var_data)
            assert isinstance(var_elem, Variable), f"var_elem in UnitBlock {var_elem.__class__.__name__} is not an Variable"
            unit.add_variable(var_elem)
        
        for au_data in data.get("atomic_units", []):
            au_elem = element_from_dict(au_data)
            assert isinstance(au_elem, AtomicUnit), f"au_data in UnitBlock {au_elem.__class__.__name__} is not an AtomicUnit"
            unit.add_atomic_unit(au_elem)
        
        for ub_data in data.get("unit_blocks", []):
            ub_elem = element_from_dict(ub_data)
            assert isinstance(ub_elem, UnitBlock), f"ub_elem in UnitBlock {ub_elem.__class__.__name__} is not an UnitBlock"
            unit.add_unit_block(ub_elem)
        
        for dep_data in data.get("dependencies", []):
            dep_elem = element_from_dict(dep_data)
            assert isinstance(dep_elem, Dependency), f"dep_data in UnitBlock {dep_elem.__class__.__name__} is not an Dependency"
            unit.add_dependency(dep_elem)
        
        unit.path = data.get("path", "")
        return unit
    
    elif ir_type == "Dependency":
        # Dont know if Info is needed
        return Dependency(data.get("names", []))
    
    else:
        # Unknown type: treat as generic CodeElement
        return CodeElement(info)
