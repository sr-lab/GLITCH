import unittest
from glitch.parsers.ansible import AnsibleParser
from glitch.parsers.chef import ChefParser
from glitch.parsers.puppet import PuppetParser
from glitch.parsers.parser import Parser
from glitch.repr.inter import *
from typing import Any, Dict, Sequence, List


def simplify_kvs(ir: Sequence[KeyValue]) -> List[Dict[Any, Any]]:
    def simplify_dict(kv_dict: Dict[Any, Any]) -> None:
        for key, value in list(kv_dict.items()):
            if key in ["line", "column", "end_line", "end_column"]:
                del kv_dict[key]
                continue

            if isinstance(value, dict):
                simplify_dict(value)  # type: ignore
            elif isinstance(value, list):
                for i, item in enumerate(value):  # type: ignore
                    if isinstance(item, dict):
                        simplify_dict(item)  # type: ignore

    res: List[Dict[Any, Any]] = []
    for kv in ir:
        kv_dict = kv.as_dict()
        res.append(kv_dict)
        simplify_dict(kv_dict)

    return res


class TestHierarchicalParsers(unittest.TestCase):
    def _test_parse_vars(
        self,
        path: str,
        parser: Parser,
        block_type: UnitBlockType,
        expected: List[Dict[Any, Any]],
    ) -> None:
        unitblock = parser.parse_file(path, block_type)
        assert unitblock is not None
        self.assertEqual(simplify_kvs(unitblock.variables), expected)


class TestHierarchicalAnsible(TestHierarchicalParsers):
    def test_hierarchical_vars_ansible(self) -> None:
        self._test_parse_vars(
            "tests/hierarchical/ansible/vars.yml",
            AnsibleParser(),
            UnitBlockType.unknown,
            [
                {
                    "ir_type": "Variable",
                    "code": "test:\n",
                    "name": "test",
                    "value": {
                        "ir_type": "Array",
                        "code": "  - test1:\n    - [1, 2]\n  - [3, 4]\n  - x\n  - y\n  - 23\n\n",
                        "value": [
                            {
                                "ir_type": "Hash",
                                "code": "  - test1:\n    - [1, 2]\n  ",
                                "value": [
                                    {
                                        "key": {
                                            "ir_type": "String",
                                            "code": "test1",
                                            "value": "test1",
                                        },
                                        "value": {
                                            "ir_type": "Array",
                                            "code": "    - [1, 2]\n  ",
                                            "value": [
                                                {
                                                    "ir_type": "Array",
                                                    "code": "[1, 2]",
                                                    "value": [
                                                        {
                                                            "ir_type": "Integer",
                                                            "code": "1",
                                                            "value": 1,
                                                        },
                                                        {
                                                            "ir_type": "Integer",
                                                            "code": "2",
                                                            "value": 2,
                                                        },
                                                    ],
                                                }
                                            ],
                                        },
                                    }
                                ],
                            },
                            {
                                "ir_type": "Array",
                                "code": "[3, 4]",
                                "value": [
                                    {"ir_type": "Integer", "code": "3", "value": 3},
                                    {"ir_type": "Integer", "code": "4", "value": 4},
                                ],
                            },
                            {"ir_type": "String", "code": "x", "value": "x"},
                            {"ir_type": "String", "code": "y", "value": "y"},
                            {"ir_type": "Integer", "code": "23", "value": 23},
                        ],
                    },
                },
                {
                    "ir_type": "Variable",
                    "code": "test2:\n",
                    "name": "test2",
                    "value": {
                        "ir_type": "Array",
                        "code": "  - [2, 5, 6]\n\n",
                        "value": [
                            {
                                "ir_type": "Array",
                                "code": "[2, 5, 6]",
                                "value": [
                                    {"ir_type": "Integer", "code": "2", "value": 2},
                                    {"ir_type": "Integer", "code": "5", "value": 5},
                                    {"ir_type": "Integer", "code": "6", "value": 6},
                                ],
                            }
                        ],
                    },
                },
                {
                    "ir_type": "Variable",
                    "code": "vars:\n",
                    "name": "vars",
                    "value": {
                        "ir_type": "Hash",
                        "code": "  factorial_of: 5\n  factorial_value: 1",
                        "value": [
                            {
                                "key": {
                                    "ir_type": "String",
                                    "code": "factorial_of",
                                    "value": "factorial_of",
                                },
                                "value": {
                                    "ir_type": "Integer",
                                    "code": "5",
                                    "value": 5,
                                },
                            },
                            {
                                "key": {
                                    "ir_type": "String",
                                    "code": "factorial_value",
                                    "value": "factorial_value",
                                },
                                "value": {
                                    "ir_type": "Integer",
                                    "code": "1",
                                    "value": 1,
                                },
                            },
                        ],
                    },
                },
            ],
        )

    def test_hierarchical_attributes_ansible(self) -> None:
        unitblock = AnsibleParser().parse_file(
            "tests/hierarchical/ansible/attributes.yml", UnitBlockType.unknown
        )
        assert unitblock is not None
        assert len(unitblock.atomic_units) == 1
        self.assertEqual(
            simplify_kvs(unitblock.atomic_units[0].attributes),
            [
                {
                    "ir_type": "Attribute",
                    "code": 'msg: "The factorial of 5 is {{ factorial_value }}"',
                    "name": "msg",
                    "value": {
                        "ir_type": "Sum",
                        "code": '"The factorial of 5 is {{ factorial_value }}"',
                        "left": {
                            "ir_type": "String",
                            "code": '"The factorial of 5 is ',
                            "value": "The factorial of 5 is ",
                        },
                        "right": {
                            "ir_type": "VariableReference",
                            "code": 'factorial_value }}"',
                            "value": "factorial_value",
                        },
                        "type": "sum",
                    },
                },
                {
                    "ir_type": "Attribute",
                    "code": 'seq: [test: "something", "y", "z"]',
                    "name": "seq",
                    "value": {
                        "ir_type": "Array",
                        "code": '[test: "something", "y", "z"]',
                        "value": [
                            {
                                "ir_type": "Hash",
                                "code": 'test: "something"',
                                "value": [
                                    {
                                        "key": {
                                            "ir_type": "String",
                                            "code": "test",
                                            "value": "test",
                                        },
                                        "value": {
                                            "ir_type": "String",
                                            "code": '"something"',
                                            "value": "something",
                                        },
                                    }
                                ],
                            },
                            {"ir_type": "String", "code": '"y"', "value": "y"},
                            {"ir_type": "String", "code": '"z"', "value": "z"},
                        ],
                    },
                },
                {
                    "ir_type": "Attribute",
                    "code": 'hash: {test1: "1", test2: "2"}',
                    "name": "hash",
                    "value": {
                        "ir_type": "Hash",
                        "code": '{test1: "1", test2: "2"}',
                        "value": [
                            {
                                "key": {
                                    "ir_type": "String",
                                    "code": "test1",
                                    "value": "test1",
                                },
                                "value": {
                                    "ir_type": "String",
                                    "code": '"1"',
                                    "value": "1",
                                },
                            },
                            {
                                "key": {
                                    "ir_type": "String",
                                    "code": "test2",
                                    "value": "test2",
                                },
                                "value": {
                                    "ir_type": "String",
                                    "code": '"2"',
                                    "value": "2",
                                },
                            },
                        ],
                    },
                },
            ],
        )


class TestHierarchicalPuppet(TestHierarchicalParsers):
    def test_hierarchical_vars_puppet(self) -> None:
        self._test_parse_vars(
            "tests/hierarchical/puppet/vars.pp",
            PuppetParser(),
            UnitBlockType.script,
            [
                {
                    "ir_type": "Variable",
                    "code": "$my_hash = {\n'key1' => {\n    'test1' => '1',\n    'test2' => '2',\n    },\n'key2' => 'value2',\n'key3' => 'value3',\n}",
                    "name": "my_hash",
                    "value": {
                        "ir_type": "Hash",
                        "code": "$my_hash = {\n'key1' => {\n    'test1' => '1',\n    'test2' => '2',\n    },\n'key2' => 'value2',\n'key3' => 'value3',\n}",
                        "value": [
                            {
                                "key": {
                                    "ir_type": "String",
                                    "code": "'key1'",
                                    "value": "key1",
                                },
                                "value": {
                                    "ir_type": "Hash",
                                    "code": "'key1' => {\n    'test1' => '1',\n    'test2' => '2',\n    }",
                                    "value": [
                                        {
                                            "key": {
                                                "ir_type": "String",
                                                "code": "'test1'",
                                                "value": "test1",
                                            },
                                            "value": {
                                                "ir_type": "String",
                                                "code": "'1'",
                                                "value": "1",
                                            },
                                        },
                                        {
                                            "key": {
                                                "ir_type": "String",
                                                "code": "'test2'",
                                                "value": "test2",
                                            },
                                            "value": {
                                                "ir_type": "String",
                                                "code": "'2'",
                                                "value": "2",
                                            },
                                        },
                                    ],
                                },
                            },
                            {
                                "key": {
                                    "ir_type": "String",
                                    "code": "'key2'",
                                    "value": "key2",
                                },
                                "value": {
                                    "ir_type": "String",
                                    "code": "'value2'",
                                    "value": "value2",
                                },
                            },
                            {
                                "key": {
                                    "ir_type": "String",
                                    "code": "'key3'",
                                    "value": "key3",
                                },
                                "value": {
                                    "ir_type": "String",
                                    "code": "'value3'",
                                    "value": "value3",
                                },
                            },
                        ],
                    },
                },
                {
                    "ir_type": "Variable",
                    "code": "$my_hash['key4']['key5'] = 'value5'",
                    "name": "my_hash['key4']['key5']",
                    "value": {
                        "ir_type": "String",
                        "code": "'value5'",
                        "value": "value5",
                    },
                },
                {
                    "ir_type": "Variable",
                    "code": '$configdir         = "${boxen::config::configdir}/php"',
                    "name": "configdir",
                    "value": {
                        "ir_type": "Sum",
                        "code": '"${boxen::config::configdir}/php"',
                        "left": {
                            "ir_type": "VariableReference",
                            "code": "boxen::config::configdir",
                            "value": "boxen::config::configdir",
                        },
                        "right": {
                            "ir_type": "String",
                            "code": '"${boxen::config::configdir}/php"',
                            "value": "/php",
                        },
                        "type": "sum",
                    },
                },
                {
                    "ir_type": "Variable",
                    "code": '$datadir           = "${boxen::config::datadir}/php"',
                    "name": "datadir",
                    "value": {
                        "ir_type": "Sum",
                        "code": '"${boxen::config::datadir}/php"',
                        "left": {
                            "ir_type": "VariableReference",
                            "code": "boxen::config::datadir",
                            "value": "boxen::config::datadir",
                        },
                        "right": {
                            "ir_type": "String",
                            "code": '"${boxen::config::datadir}/php"',
                            "value": "/php",
                        },
                        "type": "sum",
                    },
                },
                {
                    "ir_type": "Variable",
                    "code": '$pluginsdir        = "${root}/plugins"',
                    "name": "pluginsdir",
                    "value": {
                        "ir_type": "Sum",
                        "code": '"${root}/plugins"',
                        "left": {
                            "ir_type": "VariableReference",
                            "code": "root",
                            "value": "root",
                        },
                        "right": {
                            "ir_type": "String",
                            "code": '"${root}/plugins"',
                            "value": "/plugins",
                        },
                        "type": "sum",
                    },
                },
                {
                    "ir_type": "Variable",
                    "code": '$cachedir          = "${php::config::datadir}/cache"',
                    "name": "cachedir",
                    "value": {
                        "ir_type": "Sum",
                        "code": '"${php::config::datadir}/cache"',
                        "left": {
                            "ir_type": "VariableReference",
                            "code": "php::config::datadir",
                            "value": "php::config::datadir",
                        },
                        "right": {
                            "ir_type": "String",
                            "code": '"${php::config::datadir}/cache"',
                            "value": "/cache",
                        },
                        "type": "sum",
                    },
                },
                {
                    "ir_type": "Variable",
                    "code": '$extensioncachedir = "${php::config::datadir}/cache/extensions"',
                    "name": "extensioncachedir",
                    "value": {
                        "ir_type": "Sum",
                        "code": '"${php::config::datadir}/cache/extensions"',
                        "left": {
                            "ir_type": "VariableReference",
                            "code": "php::config::datadir",
                            "value": "php::config::datadir",
                        },
                        "right": {
                            "ir_type": "String",
                            "code": '"${php::config::datadir}/cache/extensions"',
                            "value": "/cache/extensions",
                        },
                        "type": "sum",
                    },
                },
            ],
        )


class TestHierarchicalChef(TestHierarchicalParsers):
    def test_hierarchical_vars_chef(self) -> None:
        self._test_parse_vars(
            "tests/hierarchical/chef/vars.rb",
            ChefParser(),
            UnitBlockType.script,
            [
                {
                    "ir_type": "Variable",
                    "code": "grades",
                    "name": "grades",
                    "value": {
                        "ir_type": "Hash",
                        "code": '{ "Jane Doe" => 10, "Jim Doe" => 6 }',
                        "value": [
                            {
                                "key": {
                                    "ir_type": "String",
                                    "code": "Jane Doe",
                                    "value": "Jane Doe",
                                },
                                "value": {
                                    "ir_type": "Integer",
                                    "code": "10",
                                    "value": 10,
                                },
                            },
                            {
                                "key": {
                                    "ir_type": "String",
                                    "code": "Jim Doe",
                                    "value": "Jim Doe",
                                },
                                "value": {
                                    "ir_type": "Integer",
                                    "code": "6",
                                    "value": 6,
                                },
                            },
                        ],
                    },
                },
                {
                    "ir_type": "Variable",
                    "code": "default[:zabbix][:database][:password]",
                    "name": "default[:zabbix][:database][:password]",
                    "value": {
                        "ir_type": "VariableReference",
                        "code": "nil",
                        "value": "nil",
                    },
                },
                {
                    "ir_type": "Variable",
                    "code": "default[:zabbix][:test][:name]",
                    "name": "default[:zabbix][:test][:name]",
                    "value": {
                        "ir_type": "String",
                        "code": "something",
                        "value": "something",
                    },
                },
            ],
        )
