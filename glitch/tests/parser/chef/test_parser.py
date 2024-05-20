from glitch.parsers.chef import ChefParser
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

    def __check_key_value(
        self,
        key_value: KeyValue,
        line: int,
        column: int,
        end_line: int,
        end_column: int,
    ) -> None:
        assert key_value.line == line
        assert key_value.end_line == end_line
        assert key_value.column == column
        assert key_value.end_column == end_column

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
        assert (
            ir.atomic_units[0].name == "create ssh keypair for #{new_resource.username}"
        )
        assert ir.atomic_units[0].type == "execute"
        assert len(ir.atomic_units[0].attributes) == 3

        assert isinstance(ir.atomic_units[0].attributes[0], Attribute)
        self.__check_key_value(ir.atomic_units[0].attributes[0], 4, 5, 4, 36)
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
        self.__check_key_value(ir.atomic_units[0].attributes[1], 5, 5, 9, 45)
        assert ir.atomic_units[0].attributes[1].name == "command"
        assert isinstance(ir.atomic_units[0].attributes[1].value, MethodCall)
        self._check_value(
            ir.atomic_units[0].attributes[1].value.receiver,
            String,
            "      ssh-keygen -t dsa -f #{my_home}/.ssh/id_dsa -N '' \\\n        -C '#{new_resource.username}@#{fqdn}-#{Time.now.strftime('%FT%T%z')}'\n      chmod 0600 #{my_home}/.ssh/id_dsa\n      chmod 0644 #{my_home}/.ssh/id_dsa.pub\n",
            6,
            1,
            9,
            45,
        )
        assert ir.atomic_units[0].attributes[1].value.method == "gsub"
        assert len(ir.atomic_units[0].attributes[1].value.args) == 2
        self._check_value(
            ir.atomic_units[0].attributes[1].value.args[0], String, "^ +/", 5, 31, 5, 35
        )
        assert isinstance(ir.atomic_units[0].attributes[1].value.args[1], String)

        assert isinstance(ir.atomic_units[0].attributes[2], Attribute)
        self.__check_key_value(ir.atomic_units[0].attributes[2], 11, 5, 11, 23)
        assert ir.atomic_units[0].attributes[2].name == "action"
        self._check_value(
            ir.atomic_units[0].attributes[2].value,
            VariableReference,
            ":nothing",
            11,
            15,
            11,
            23,
        )

    def test_chef_parser_alias(self) -> None:
        # TODO: support alias
        ir = self.__parse("tests/parser/chef/files/alias.rb")
        assert len(ir.variables) == 0

    def test_chef_parser_aref(self) -> None:
        """
        aref | aref_field | @int
        """
        ir = self.__parse("tests/parser/chef/files/aref.rb")
        assert len(ir.variables) == 1
        assert isinstance(ir.variables[0], Variable)
        assert ir.variables[0].name == "collection[0]"
        self.__check_key_value(ir.variables[0], 1, 1, 1, 30)
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

    def test_chef_parser_args_add(self) -> None:
        """
        args_add_star | args_forward | fcall | tstring_content
        """
        ir = self.__parse("tests/parser/chef/files/args_add.rb")
        assert len(ir.variables) == 2

        assert isinstance(ir.variables[0], Variable)
        assert ir.variables[0].name == "x"
        self.__check_key_value(ir.variables[0], 2, 5, 2, 20)
        assert isinstance(ir.variables[0].value, FunctionCall)
        assert len(ir.variables[0].value.args) == 2
        for i in range(2):
            assert isinstance(ir.variables[0].value.args[i], VariableReference)

        assert isinstance(ir.variables[1], Variable)
        assert ir.variables[1].name == "x"
        self.__check_key_value(ir.variables[1], 3, 5, 3, 16)  # FIXME should be 20
        assert isinstance(ir.variables[1].value, FunctionCall)
        assert len(ir.variables[1].value.args) == 1
        assert isinstance(ir.variables[1].value.args[0], Null)

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

        self.__check_key_value(
            ir.variables[0], 1, 1, 1, 2
        )  # FIXME should be 1, 1, 1, 7
        self.__check_key_value(ir.variables[1], 2, 1, 2, 22)
        self.__check_key_value(ir.variables[2], 3, 1, 3, 23)
        for i in range(3, 7):
            self.__check_key_value(ir.variables[i], i + 1, 1, i + 1, 22)

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
        print(ir.variables[7].value.value[0].right.line)
        print(ir.variables[7].value.value[0].right.column)
        print(ir.variables[7].value.value[0].right.end_line)
        print(ir.variables[7].value.value[0].right.end_column)
        print(ir.variables[7].value.value[0].right.value)
        self._check_binary_operation(
            ir.variables[7].value.value[0],
            Sum,
            String("three", ElementInfo(8, 8, 8, 13, "three")),
            VariableReference("four", ElementInfo(8, 15, 8, 19, "four")),
            8,
            8,
            8,
            20,
        )


# TODO: test inline resource
# TODO: test append strings with interpolation
