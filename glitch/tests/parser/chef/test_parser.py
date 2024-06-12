from glitch.parsers.chef import ChefParser, AddArgs
from glitch.repr.inter import *
from glitch.tests.parser.test_parser import TestParser


class TestChefParser(TestParser):
    def __parse(self, file: str) -> UnitBlock:
        p = ChefParser()
        ir = p.parse_file(file, UnitBlockType.script)
        assert ir is not None
        assert isinstance(ir, UnitBlock)
        assert ir.type == UnitBlockType.script
        return ir

    def __check_code_element(
        self,
        code_element: CodeElement,
        line: int,
        column: int,
        end_line: int,
        end_column: int,
    ) -> None:
        assert code_element.line == line
        assert code_element.end_line == end_line
        assert code_element.column == column
        assert code_element.end_column == end_column

    def test_chef_parser_valid_manifest(self) -> None:
        """
        string_literal | regexp_literal | vcall | symbol_literal | @ident
        call | args_add_block | arg_paren | @period | method_add_arg
        """

        ir = self.__parse("tests/parser/chef/files/valid_manifest.rb")
        assert len(ir.variables) == 1
        assert len(ir.atomic_units) == 1

        assert isinstance(ir.variables[0], Variable)
        assert ir.variables[0].name == "my_home"
        self._check_value(ir.variables[0].value, String, "/home/test", 1, 11, 1, 23)
        assert ir.variables[0].line == 1
        assert ir.variables[0].column == 1
        assert ir.variables[0].end_line == 1
        assert ir.variables[0].end_column == 23

        assert isinstance(ir.atomic_units[0], AtomicUnit)
        assert isinstance(ir.atomic_units[0].name, Sum)
        assert isinstance(ir.atomic_units[0].name.left, String)
        assert ir.atomic_units[0].name.left.value == "create ssh keypair for "
        assert isinstance(ir.atomic_units[0].name.right, VariableReference)
        assert ir.atomic_units[0].name.right.value == "new_resource.username"
        assert ir.atomic_units[0].type == "execute"
        assert len(ir.atomic_units[0].attributes) == 3

        assert isinstance(ir.atomic_units[0].attributes[0], Attribute)
        self.__check_code_element(ir.atomic_units[0].attributes[0], 4, 5, 4, 36)
        assert ir.atomic_units[0].attributes[0].name == "user"
        assert isinstance(ir.atomic_units[0].attributes[0].value, MethodCall)
        self._check_value(
            ir.atomic_units[0].attributes[0].value.receiver,
            VariableReference,
            "new_resource",
            4,
            15,
            4,
            27,
        )
        assert ir.atomic_units[0].attributes[0].value.method == "username"
        assert len(ir.atomic_units[0].attributes[0].value.args) == 0

        assert isinstance(ir.atomic_units[0].attributes[1], Attribute)
        self.__check_code_element(ir.atomic_units[0].attributes[1], 5, 5, 5, 21)
        assert ir.atomic_units[0].attributes[1].name == "command"
        self._check_value(
            ir.atomic_units[0].attributes[1].value,
            String,
            "test",
            5,
            15,
            5,
            21,
        )

        assert isinstance(ir.atomic_units[0].attributes[2], Attribute)
        self.__check_code_element(ir.atomic_units[0].attributes[2], 6, 5, 6, 23)
        assert ir.atomic_units[0].attributes[2].name == "action"
        self._check_value(
            ir.atomic_units[0].attributes[2].value,
            VariableReference,
            ":nothing",
            6,
            15,
            6,
            23,
        )

    def test_chef_parser_mix(self) -> None:
        """
        alias | next | module | oct integer | yield | assign | backref | @const
        binary | sclass
        """
        # TODO: support alias
        ir = self.__parse("tests/parser/chef/files/mix.rb")
        assert len(ir.variables) == 10
        assert len(ir.unit_blocks) == 1

        assert isinstance(ir.variables[0], Variable)
        assert ir.variables[0].name == "x"
        assert isinstance(ir.variables[0].value, FunctionCall)
        assert ir.variables[0].value.name == "next"
        self.__check_code_element(
            ir.variables[0].value, 2, 10, 2, 15
        )  # FIXME: should be 2, 5, 2, 14

        assert isinstance(ir.variables[1], Variable)
        assert isinstance(ir.variables[1].value, Null)  # FIXME

        assert isinstance(ir.variables[2], Variable)
        assert isinstance(ir.variables[2].value, Null)  # FIXME

        assert isinstance(ir.variables[3], Variable)
        assert isinstance(ir.variables[3].value, Null)  # FIXME

        assert isinstance(ir.variables[4], Variable)
        assert isinstance(ir.variables[4].value, Assign)

        assert isinstance(ir.variables[5], Variable)
        assert isinstance(ir.variables[5].value, ConditionalStatement)

        assert isinstance(ir.variables[6], Variable)
        assert isinstance(ir.variables[6].value, MethodCall)

        assert isinstance(ir.variables[7], Variable)
        assert isinstance(ir.variables[7].value, Integer)
        assert ir.variables[7].value.value == 0x0D000004

        assert isinstance(ir.variables[8], Variable)
        assert isinstance(ir.variables[8].value, Null)  # FIXME

        assert isinstance(ir.unit_blocks[0], UnitBlock)
        assert ir.unit_blocks[0].type == UnitBlockType.block
        assert ir.unit_blocks[0].name == "Namespace"
        assert len(ir.unit_blocks[0].variables) == 1
        self._check_value(
            ir.unit_blocks[0].variables[0].value, Integer, 0o640, 7, 5, 7, 10
        )

    def test_chef_parser_aref(self) -> None:
        """
        aref | aref_field | @int | ||=
        """
        ir = self.__parse("tests/parser/chef/files/aref.rb")
        assert len(ir.variables) == 2
        assert isinstance(ir.variables[0], Variable)
        self.__check_code_element(ir.variables[0], 1, 1, 1, 30)
        assert ir.variables[0].name == "collection[0]"
        self._check_binary_operation(
            ir.variables[0].value,
            Access,
            VariableReference("collection", ElementInfo(1, 17, 1, 27, "collection")),
            Integer(1, ElementInfo(1, 28, 1, 29, "1")),
            1,
            17,
            1,
            30,
        )

        assert isinstance(ir.variables[1], Variable)
        assert isinstance(ir.variables[1].value, ConditionalStatement)

    def test_chef_parser_args_add(self) -> None:
        """
        args_add_star | args_forward | fcall | tstring_content |
        command | command_call | const_path | const_path_ref | cvar
        """
        ir = self.__parse("tests/parser/chef/files/args_add.rb")
        assert len(ir.unit_blocks) == 1
        assert len(ir.unit_blocks[0].variables) == 4

        assert isinstance(ir.unit_blocks[0].variables[0], Variable)
        assert ir.unit_blocks[0].variables[0].name == "x"
        self.__check_code_element(ir.unit_blocks[0].variables[0], 2, 5, 2, 21)
        assert isinstance(ir.unit_blocks[0].variables[0].value, FunctionCall)
        assert len(ir.unit_blocks[0].variables[0].value.args) == 2
        for i in range(2):
            assert isinstance(
                ir.unit_blocks[0].variables[0].value.args[i], VariableReference
            )

        assert isinstance(ir.unit_blocks[0].variables[1], Variable)
        assert ir.unit_blocks[0].variables[1].name == "x"
        self.__check_code_element(
            ir.unit_blocks[0].variables[1], 3, 5, 3, 16
        )  # FIXME should be 20
        assert isinstance(ir.unit_blocks[0].variables[1].value, FunctionCall)
        assert len(ir.unit_blocks[0].variables[1].value.args) == 1
        assert isinstance(ir.unit_blocks[0].variables[1].value.args[0], Null)

        assert isinstance(ir.unit_blocks[0].variables[2], Variable)
        assert ir.unit_blocks[0].variables[2].name == "x"
        self.__check_code_element(ir.unit_blocks[0].variables[2], 4, 5, 4, 36)
        assert isinstance(ir.unit_blocks[0].variables[2].value, FunctionCall)
        assert len(ir.unit_blocks[0].variables[2].value.args) == 3
        assert isinstance(ir.unit_blocks[0].variables[2].value.args[2], FunctionCall)
        assert ir.unit_blocks[0].variables[2].value.args[2].name == "defined"

        assert isinstance(ir.unit_blocks[0].variables[3], Variable)
        assert ir.unit_blocks[0].variables[3].name == "x"
        self.__check_code_element(ir.unit_blocks[0].variables[3], 5, 5, 5, 34)
        assert isinstance(ir.unit_blocks[0].variables[3].value, MethodCall)
        assert len(ir.unit_blocks[0].variables[3].value.args) == 2

    def test_chef_parser_array(self) -> None:
        """
        array | qwords_add | qwords_new | qsymbols_add | qsymbols_new
        words_add | words_new | word_add | symbols_add | symbols_new | string_embexpr
        """
        ir = self.__parse("tests/parser/chef/files/array.rb")
        assert len(ir.variables) == 8
        for i in range(7):
            assert isinstance(ir.variables[i], Variable)
            assert ir.variables[i].name == "y"

        self.__check_code_element(
            ir.variables[0], 1, 1, 1, 2
        )  # FIXME should be 1, 1, 1, 7
        self.__check_code_element(ir.variables[1], 2, 1, 2, 22)
        self.__check_code_element(ir.variables[2], 3, 1, 3, 23)
        self.__check_code_element(ir.variables[3], 4, 1, 8, 6)
        for i in range(4, 7):
            self.__check_code_element(ir.variables[i], i + 5, 1, i + 5, 22)

        for i in range(7):
            assert isinstance(ir.variables[i].value, Array)

        assert len(ir.variables[0].value.value) == 0  # type: ignore
        for i in range(1, 7):
            assert len(ir.variables[i].value.value) == 3  # type: ignore

        for i in range(3):
            assert isinstance(ir.variables[1].value.value[i], VariableReference)  # type: ignore
            assert isinstance(ir.variables[2].value.value[i], VariableReference)  # type: ignore
            assert isinstance(ir.variables[3].value.value[i], String)  # type: ignore
            assert isinstance(ir.variables[4].value.value[i], String)  # type: ignore
            assert isinstance(ir.variables[5].value.value[i], String)  # type: ignore
            assert isinstance(ir.variables[6].value.value[i], String)  # type: ignore

        assert isinstance(ir.variables[7], Variable)
        assert isinstance(ir.variables[7].value, Array)
        assert len(ir.variables[7].value.value) == 1
        self._check_binary_operation(
            ir.variables[7].value.value[0],
            Sum,
            String("three", ElementInfo(12, 8, 12, 13, "three")),
            VariableReference("four", ElementInfo(12, 15, 12, 19, "four")),
            12,
            8,
            12,
            20,
        )

    def test_chef_parser_hash(self) -> None:
        """
        hash | assoclist_from_args | assoc_splat | assoc_new | var_ref | backref |
        backtick | xstring_literal | bare_assoc_hash | begin | end
        """
        ir = self.__parse("tests/parser/chef/files/hash.rb")
        assert len(ir.variables) == 4
        assert isinstance(ir.variables[0], Variable)
        assert ir.variables[0].name == "x"
        self.__check_code_element(ir.variables[0], 1, 1, 5, 2)
        assert isinstance(ir.variables[0].value, Hash)
        self.__check_code_element(ir.variables[0].value, 1, 5, 5, 2)

        assert len(ir.variables[0].value.value) == 3
        for i in range(3):
            assert isinstance(
                list(ir.variables[0].value.value.keys())[i], VariableReference
            )
        assert isinstance(
            list(ir.variables[0].value.value.values())[0], VariableReference
        )
        assert isinstance(list(ir.variables[0].value.value.values())[1], String)
        self._check_value(
            list(ir.variables[0].value.value.values())[2],
            String,
            "echo $a",
            4,
            10,
            4,
            19,
        )

        assert isinstance(ir.variables[1], Variable)
        assert ir.variables[1].name == "y"
        self.__check_code_element(
            ir.variables[1], 6, 1, 6, 2
        )  # FIXME: should be 5, 1, 5, 7
        assert isinstance(ir.variables[1].value, Hash)
        assert len(ir.variables[1].value.value) == 0

        assert isinstance(ir.variables[2], Variable)
        assert ir.variables[2].name == "z"
        self.__check_code_element(ir.variables[2], 7, 1, 7, 12)
        assert isinstance(ir.variables[2].value, Hash)
        assert len(ir.variables[2].value.value) == 1
        # FIXME: splat
        assert isinstance(
            list(ir.variables[2].value.value.keys())[0], VariableReference
        )
        assert isinstance(
            list(ir.variables[2].value.value.values())[0], VariableReference
        )

        assert isinstance(ir.variables[3], Variable)
        assert ir.variables[3].name == "w"
        self.__check_code_element(ir.variables[3], 9, 1, 9, 39)
        assert isinstance(ir.variables[3].value, FunctionCall)
        assert isinstance(ir.variables[3].value.args[0], Hash)

    def test_chef_parser_binary(self) -> None:
        """
        binary | dot2 | dot3 | paren | stmts_add
        """
        ir = self.__parse("tests/parser/chef/files/binary.rb")
        assert len(ir.variables) == 25
        for i in range(25):
            assert isinstance(ir.variables[i], Variable)
            assert ir.variables[i].name == chr(ord("a") + i)

        tests = [
            (Sum, 0),
            (Subtract, 0),
            (Multiply, 0),
            (Divide, 0),
            (Modulo, 0),
            (Power, 1),
            (Equal, 1),
            (NotEqual, 1),
            (GreaterThan, 0),
            (LessThan, 0),
            (GreaterThanOrEqual, 1),
            (LessThanOrEqual, 1),
            (None, 1),  # FIXME
            (Equal, 2),
            (BitwiseAnd, 0),
            (BitwiseOr, 0),
            (BitwiseXor, 0),
            (LeftShift, 1),
            (RightShift, 1),
            (And, 2),
            (Or, 1),
        ]
        for i, test in enumerate(tests):
            type, offset = test
            paren_offset = 0 if type not in (And, Or) else 1
            if type is None:
                continue

            self._check_binary_operation(
                ir.variables[i].value,
                type,
                Integer(
                    1,
                    ElementInfo(i + 1, 5 + paren_offset, i + 1, 6 + paren_offset, "1"),
                ),
                Integer(
                    2,
                    ElementInfo(
                        i + 1,
                        9 + offset + paren_offset,
                        i + 1,
                        10 + offset + paren_offset,
                        "2",
                    ),
                ),
                i + 1,
                5 + paren_offset,
                i + 1,
                10 + offset + paren_offset,
            )
        assert isinstance(ir.variables[21].value, FunctionCall)
        assert ir.variables[21].value.name == "range"
        assert isinstance(ir.variables[22].value, FunctionCall)
        assert ir.variables[22].value.name == "range"

    def test_chef_parser_case(self) -> None:
        """
        case | when | else | in | hshptn
        """
        ir = self.__parse("tests/parser/chef/files/case.rb")
        assert len(ir.statements) == 2
        assert isinstance(ir.statements[0], ConditionalStatement)
        assert isinstance(ir.statements[1], ConditionalStatement)
        assert ir.statements[0].type == ConditionalStatement.ConditionType.SWITCH
        assert ir.statements[1].type == ConditionalStatement.ConditionType.SWITCH

        self._check_binary_operation(
            ir.statements[0].condition,
            Equal,
            VariableReference("value", ElementInfo(1, 6, 1, 11, "value")),
            Integer(1, ElementInfo(2, 6, 2, 7, "1")),
            2,  # FIXME
            6,  # FIXME
            5,
            11,
        )
        assert isinstance(ir.statements[0].else_statement, ConditionalStatement)
        assert ir.statements[0].else_statement.else_statement is None

        self._check_binary_operation(
            ir.statements[1].condition,
            Equal,
            VariableReference("value", ElementInfo(8, 6, 8, 11, "value")),
            BitwiseOr(
                ElementInfo(9, 4, 9, 9, "2 | 3"),
                Integer(2, ElementInfo(9, 4, 9, 5, "2")),
                Integer(3, ElementInfo(9, 8, 9, 9, "3")),
            ),
            9,  # FIXME
            4,  # FIXME
            12,
            11,
        )
        assert isinstance(ir.statements[1].else_statement, ConditionalStatement)
        assert ir.statements[1].else_statement.else_statement is None

        assert len(ir.variables) == 1
        assert isinstance(ir.variables[0].value, ConditionalStatement)

    def test_chef_parser_if(self) -> None:
        """
        if | elsif | else | float | if_mod | ifop | imaginary | ivar | massign
        mlhs_add | mlhs_new | mrhs_add | mrhs_new | mrhs_new_from_args | mrhs_add_star
        """
        ir = self.__parse("tests/parser/chef/files/if.rb")
        assert len(ir.statements) == 1

        assert isinstance(ir.statements[0], ConditionalStatement)
        assert ir.statements[0].type == ConditionalStatement.ConditionType.IF
        assert isinstance(ir.statements[0].condition, VariableReference)
        assert len(ir.statements[0].statements) == 3

        assert isinstance(ir.statements[0].statements[0], Variable)
        self._check_value(ir.statements[0].statements[0].value, Float, 1.0, 2, 9, 2, 12)

        assert isinstance(ir.statements[0].statements[1], Variable)
        self._check_value(
            ir.statements[0].statements[1].value, VariableReference, "$v", 3, 9, 3, 11
        )

        assert isinstance(ir.statements[0].statements[2], Variable)
        assert isinstance(ir.statements[0].statements[2].value, ConditionalStatement)
        assert (
            ir.statements[0].statements[2].value.type
            == ConditionalStatement.ConditionType.IF
        )
        assert len(ir.statements[0].statements[2].value.statements) == 1
        assert isinstance(ir.statements[0].statements[2].value.statements[0], Integer)
        assert isinstance(
            ir.statements[0].statements[2].value.else_statement, ConditionalStatement
        )
        assert (
            ir.statements[0].statements[2].value.else_statement.else_statement is None
        )
        assert isinstance(
            ir.statements[0].statements[2].value.else_statement.statements[0],
            VariableReference,
        )

        assert isinstance(ir.statements[0].else_statement, ConditionalStatement)
        assert (
            ir.statements[0].else_statement.type
            == ConditionalStatement.ConditionType.IF
        )
        assert isinstance(ir.statements[0].else_statement.condition, VariableReference)
        assert len(ir.statements[0].else_statement.statements) == 1
        assert isinstance(ir.statements[0].else_statement.statements[0], Variable)
        assert isinstance(
            ir.statements[0].else_statement.statements[0].value, ConditionalStatement
        )
        assert (
            ir.statements[0].else_statement.statements[0].value.else_statement is None
        )

        else_statement = ir.statements[0].else_statement.else_statement
        assert isinstance(else_statement, ConditionalStatement)
        assert else_statement.else_statement is None
        assert len(else_statement.statements) == 3

        assert isinstance(else_statement.statements[0], Variable)
        self._check_value(else_statement.statements[0].value, Complex, 1j, 8, 9, 8, 11)

        assert isinstance(else_statement.statements[1], Variable)
        assert else_statement.statements[1].name == "first, second"

        assert isinstance(else_statement.statements[2], Variable)
        assert else_statement.statements[2].name == "value"
        assert isinstance(else_statement.statements[2].value, AddArgs)  # FIXME
        assert len(else_statement.statements[2].value.value) == 2

        assert len(ir.variables) == 1
        assert isinstance(ir.variables[0].value, ConditionalStatement)

    def test_chef_parser_opassign(self) -> None:
        """
        opassign | rational | super | top_const_ref | top_const_field
        """
        ir = self.__parse("tests/parser/chef/files/opassign.rb")
        assert len(ir.variables) == 7

        assert isinstance(ir.variables[0], Variable)
        assert ir.variables[0].name == "x"
        self._check_binary_operation(
            ir.variables[0].value,
            Sum,
            VariableReference("x", ElementInfo(1, 1, 1, 2, "x")),
            Integer(2, ElementInfo(1, 6, 1, 7, "2")),
            1,
            1,
            1,
            7,
        )

        assert isinstance(ir.variables[1], Variable)
        assert ir.variables[1].name == "::Constant"
        self._check_binary_operation(
            ir.variables[1].value,
            Subtract,
            VariableReference("::Constant", ElementInfo(2, 1, 2, 11, "::Constant")),
            Integer(2, ElementInfo(2, 15, 2, 16, "2")),
            2,
            1,
            2,
            16,
        )

        assert isinstance(ir.variables[2], Variable)
        assert ir.variables[2].name == "Constant"
        self._check_binary_operation(
            ir.variables[2].value,
            Multiply,
            VariableReference("Constant", ElementInfo(3, 1, 3, 9, "Constant")),
            VariableReference("::Test", ElementInfo(3, 13, 3, 19, "::Test")),
            3,
            1,
            3,
            19,
        )

        assert isinstance(ir.variables[3], Variable)
        assert ir.variables[3].name == "x"
        self._check_binary_operation(
            ir.variables[3].value,
            Divide,
            VariableReference("x", ElementInfo(4, 1, 4, 2, "x")),
            FunctionCall(
                "super",
                [Integer(2, ElementInfo(4, 12, 4, 13, "2"))],
                ElementInfo(4, 12, 4, 13, "super 2"),
            ),
            4,
            1,
            4,
            13,
        )
        assert ir.variables[3].value.right.name == "super"  # type: ignore

        assert isinstance(ir.variables[4], Variable)
        assert ir.variables[4].name == "x"
        self._check_binary_operation(
            ir.variables[4].value,
            Modulo,
            VariableReference("x", ElementInfo(5, 1, 5, 2, "x")),
            FunctionCall(
                "super",
                [Integer(2, ElementInfo(5, 12, 5, 13, "2"))],
                ElementInfo(5, 11, 5, 14, "super(2)"),
            ),
            5,
            1,
            5,
            14,
        )
        assert ir.variables[4].value.right.name == "super"  # type: ignore

        assert isinstance(ir.variables[5], Variable)
        assert ir.variables[5].name == "x"
        self._check_binary_operation(
            ir.variables[5].value,
            Power,
            VariableReference("x", ElementInfo(6, 1, 6, 2, "x")),
            Float(2, ElementInfo(6, 7, 6, 9, "2r")),
            6,
            1,
            6,
            9,
        )

        assert isinstance(ir.variables[6], Variable)
        assert ir.variables[6].name == "x"
        # TODO
        assert isinstance(ir.variables[6].value, Null)

    def test_chef_parser_unary(self) -> None:
        """
        unary
        """
        ir = self.__parse("tests/parser/chef/files/unary.rb")
        assert len(ir.variables) == 3

        assert isinstance(ir.variables[0], Variable)
        assert ir.variables[0].name == "x"
        assert isinstance(ir.variables[0].value, Minus)

        assert isinstance(ir.variables[1], Variable)
        assert ir.variables[1].name == "x"
        self._check_value(ir.variables[1].value, Integer, 2, 2, 5, 2, 7)

        assert isinstance(ir.variables[2], Variable)
        assert ir.variables[2].name == "x"
        assert isinstance(ir.variables[2].value, Not)

    def test_chef_parser_unless(self) -> None:
        """
        unless | unless_mod
        """
        ir = self.__parse("tests/parser/chef/files/unless.rb")
        assert len(ir.statements) == 1
        assert isinstance(ir.statements[0], ConditionalStatement)
        assert ir.statements[0].type == ConditionalStatement.ConditionType.IF
        assert isinstance(ir.statements[0].condition, Not)
        assert isinstance(ir.statements[0].condition.expr, VariableReference)
        assert len(ir.statements[0].statements) == 1
        assert isinstance(ir.statements[0].statements[0], Variable)
        assert isinstance(ir.statements[0].statements[0].value, ConditionalStatement)
        assert (
            ir.statements[0].statements[0].value.type
            == ConditionalStatement.ConditionType.IF
        )
        assert isinstance(ir.statements[0].statements[0].value.condition, Not)

        assert isinstance(ir.statements[0].else_statement, ConditionalStatement)
        assert (
            ir.statements[0].else_statement.type
            == ConditionalStatement.ConditionType.IF
        )
        assert ir.statements[0].else_statement.else_statement is None
        assert len(ir.statements[0].else_statement.statements) == 1
        assert isinstance(ir.statements[0].else_statement.statements[0], Variable)
        assert isinstance(
            ir.statements[0].else_statement.statements[0].value, FunctionCall
        )
        assert ir.statements[0].else_statement.statements[0].value.name == "zsuper"

    def test_chef_parser_class(self) -> None:
        """
        class
        """
        ir = self.__parse("tests/parser/chef/files/class.rb")
        assert len(ir.unit_blocks) == 2

        assert isinstance(ir.unit_blocks[0], UnitBlock)
        assert ir.unit_blocks[0].type == UnitBlockType.definition
        assert ir.unit_blocks[0].name == "Namespace::Container"
        assert len(ir.unit_blocks[0].variables) == 1
        assert ir.unit_blocks[0].variables[0].name == "x"
        self._check_value(ir.unit_blocks[0].variables[0].value, Integer, 1, 2, 9, 2, 10)

        assert isinstance(ir.unit_blocks[1], UnitBlock)
        assert ir.unit_blocks[1].type == UnitBlockType.definition
        assert ir.unit_blocks[1].name == "self"

    def test_chef_parser_def(self) -> None:
        """
        def | defs | lambda
        """
        ir = self.__parse("tests/parser/chef/files/def.rb")
        assert len(ir.unit_blocks) == 2

        assert isinstance(ir.unit_blocks[0], UnitBlock)
        assert ir.unit_blocks[0].type == UnitBlockType.definition
        assert ir.unit_blocks[0].name == "method"
        assert len(ir.unit_blocks[0].variables) == 1
        assert ir.unit_blocks[0].variables[0].name == "x"
        self._check_value(ir.unit_blocks[0].variables[0].value, Integer, 1, 2, 9, 2, 10)

        assert isinstance(ir.unit_blocks[1], UnitBlock)
        assert ir.unit_blocks[1].type == UnitBlockType.definition
        assert ir.unit_blocks[1].name == "object.method"
        assert len(ir.unit_blocks[1].variables) == 1
        assert ir.unit_blocks[1].variables[0].name == "x"
        self._check_value(ir.unit_blocks[1].variables[0].value, Integer, 1, 6, 9, 6, 10)

    def test_chef_parser_strings(self) -> None:
        """
        string_literal | string_add | string_embexpr | string_content
        string_dvar | embvar | regexp_add | regexp_literal
        """
        ir = self.__parse("tests/parser/chef/files/strings.rb")
        assert len(ir.variables) == 6

        assert isinstance(ir.variables[0], Variable)
        assert isinstance(ir.variables[0].value, Sum)
        assert isinstance(ir.variables[0].value.left, Sum)
        self._check_value(ir.variables[0].value.left.left, String, "test ", 1, 6, 1, 11)
        self._check_value(
            ir.variables[0].value.left.right, VariableReference, "test", 1, 13, 1, 17
        )
        self._check_value(ir.variables[0].value.right, String, " test", 1, 18, 1, 23)

        assert isinstance(ir.variables[1], Variable)
        self._check_value(
            ir.variables[1].value, VariableReference, "@test", 2, 7, 2, 12
        )

        assert isinstance(ir.variables[2], Variable)
        assert isinstance(ir.variables[2].value, MethodCall)
        assert ir.variables[2].value.method == "gsub"
        assert len(ir.variables[2].value.args) == 2
        self._check_value(ir.variables[2].value.args[0], String, "^ +", 3, 21, 3, 25)
        assert isinstance(ir.variables[2].value.args[1], String)
        assert ir.variables[2].value.args[1].value == ""

        assert isinstance(ir.variables[2].value.receiver, Sum)

        assert isinstance(ir.variables[2].value.receiver.left, Sum)
        self._check_value(
            ir.variables[2].value.receiver.right,
            String,
            "/.ssh/id_dsa.pub\n",
            5,
            22,
            6,
            1,
        )

        assert isinstance(ir.variables[2].value.receiver.left.left, Sum)
        self._check_value(
            ir.variables[2].value.receiver.left.right,
            VariableReference,
            "my_home",
            5,
            14,
            5,
            21,
        )

        assert isinstance(ir.variables[2].value.receiver.left.left.left, Sum)
        self._check_value(
            ir.variables[2].value.receiver.left.left.right,
            String,
            "/.ssh/id_dsa\nchmod 0644 ",
            4,
            22,
            5,
            12,
        )

        self._check_value(
            ir.variables[2].value.receiver.left.left.left.right,
            VariableReference,
            "my_home",
            4,
            14,
            4,
            21,
        )
        self._check_value(
            ir.variables[2].value.receiver.left.left.left.left,
            String,
            "chmod 0600 ",
            4,
            1,
            4,
            12,
        )

        assert isinstance(ir.variables[3], Variable)
        assert isinstance(ir.variables[3].value, Sum)
        self._check_value(ir.variables[3].value.right, String, " .+", 7, 16, 7, 19)

        assert isinstance(ir.variables[3].value.left, Sum)
        self._check_value(
            ir.variables[3].value.left.right, VariableReference, "test", 7, 11, 7, 15
        )
        self._check_value(ir.variables[3].value.left.left, String, ".+ ", 7, 6, 7, 9)

        assert isinstance(ir.variables[4], Variable)
        assert isinstance(ir.variables[4].value, Sum)
        self.__check_code_element(ir.variables[4].value, 8, 5, 9, 17)
        assert isinstance(ir.variables[4].value.left, String)
        assert isinstance(ir.variables[4].value.right, String)

        assert isinstance(ir.variables[5], Variable)
        assert isinstance(ir.variables[5].value, Sum)
        self._check_value(ir.variables[5].value.left, String, "echo ", 10, 6, 10, 11)
        self._check_value(
            ir.variables[5].value.right, VariableReference, "test", 10, 13, 10, 17
        )

    def test_chef_parser_string_index_out_of_range(self) -> None:
        """
        This file used to file with string index out of range.
        """
        self.__parse("tests/parser/chef/files/string_index_out_of_range.rb")

    def test_chef_parser_list_index_out_of_range(self) -> None:
        """
        This file used to file with list index out of range.
        """
        self.__parse("tests/parser/chef/files/list_index_out_of_range.rb")

    def test_chef_parser_node_object_not_subscriptable(self) -> None:
        """
        This file used to file with node object not subscriptable.
        """
        self.__parse("tests/parser/chef/files/node_object_not_subscriptable.rb")

    def test_chef_parser_do_block(self) -> None:
        """
        do_block
        """
        # TODO: For now just checks if it does not crash
        self.__parse("tests/parser/chef/files/do_block.rb")

    def test_chef_parser_brace_block(self) -> None:
        """
        brace_block
        """
        # TODO: For now just checks if it does not crash
        self.__parse("tests/parser/chef/files/brace_block.rb")

    def test_chef_parser_rescue_mod(self) -> None:
        """
        rescue_mod
        """
        ir = self.__parse("tests/parser/chef/files/rescue_mod.rb")
        assert len(ir.variables) == 1
        assert isinstance(ir.variables[0], Variable)
        assert ir.variables[0].name == "cassandra_config"
        assert isinstance(ir.variables[0].value, ConditionalStatement)

    def test_chef_parser_method_add_block(self) -> None:
        """
        method_add_block
        """
        # TODO: For now just checks if it does not crash
        self.__parse("tests/parser/chef/files/method_add_block.rb")

    def test_chef_parser_begin(self) -> None:
        """
        begin
        """
        # TODO: For now just checks if it does not crash
        self.__parse("tests/parser/chef/files/begin.rb")

    def test_chef_parser_arg_paren(self) -> None:
        """
        arg_paren
        """
        ir = self.__parse("tests/parser/chef/files/arg_paren.rb")
        assert len(ir.variables) == 1
        assert isinstance(ir.variables[0], Variable)
        assert isinstance(ir.variables[0].value, FunctionCall)

    def test_chef_parser_field(self) -> None:
        """
        field
        """
        ir = self.__parse("tests/parser/chef/files/field.rb")
        assert len(ir.variables) == 1
        assert isinstance(ir.variables[0], Variable)


# TODO:
# block_var
# blockarg
# bodystmt
# break
# aryptn
# class
# const_ref
# const_path_field
# fndptn
# for
# mlhs_add_post
# mlhs_add_star
# mlhs_paren
# nokw_param
# operator_ambiguous
# redo
# rescue
# retry
# return
# return 0
# undef
# until
# var_alias
# while
# lambda
# tlambda
