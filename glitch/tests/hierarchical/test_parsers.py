import unittest
from glitch.parsers.ansible import AnsibleParser
from glitch.parsers.chef import ChefParser
from glitch.parsers.puppet import PuppetParser


class TestAnsible(unittest.TestCase):
    def __test_parse_vars(self, path, vars) -> None:
        with open(path, "r") as file:
            unitblock = AnsibleParser._AnsibleParser__parse_vars_file(
                self, "test", file
            )
            self.assertEqual(str(unitblock.variables), vars)
        file.close()

    def __test_parse_attributes(self, path, attributes) -> None:
        with open(path, "r") as file:
            unitblock = AnsibleParser._AnsibleParser__parse_playbook(self, "test", file)
            play = unitblock.unit_blocks[0]
            self.assertEqual(str(play.attributes), attributes)
        file.close()

    def test_hierarchichal_vars(self) -> None:
        vars = "[test[0]:None:[test1[0]:\"['1', '2']\"], test[1]:\"['3', '4']\", test:\"['x', 'y', '23']\", test2[0]:\"['2', '5', '6']\", vars:None:[factorial_of:'5', factorial_value:'1']]"
        self.__test_parse_vars("tests/hierarchical/ansible/vars.yml", vars)

    def test_hierarchical_attributes(self) -> None:
        attributes = "[hosts:'localhost', debug:None:[msg:'The factorial of 5 is {{ factorial_value }}', seq[0]:None:[test:'something'], seq:\"['y', 'z']\", hash:None:[test1:'1', test2:'2']]]"
        self.__test_parse_attributes(
            "tests/hierarchical/ansible/attributes.yml", attributes
        )


class TestPuppet(unittest.TestCase):
    def __test_parse_vars(self, path, vars) -> None:
        unitblock = PuppetParser().parse_file(path, None)
        self.assertEqual(str(unitblock.variables), vars)

    def test_hierarchical_vars(self) -> None:
        vars = "[$my_hash:None:[key1:None:[test1:'1', test2:'2'], key2:'value2', key3:'value3', key4:None:[key5:'value5']], $configdir:'${boxen::config::configdir}/php', $datadir:'${boxen::config::datadir}/php', $pluginsdir:'${root}/plugins', $cachedir:'${php::config::datadir}/cache', $extensioncachedir:'${php::config::datadir}/cache/extensions']"
        self.__test_parse_vars("tests/hierarchical/puppet/vars.pp", vars)


class TestChef(unittest.TestCase):
    def __test_parse_vars(self, path, vars) -> None:
        unitblock = ChefParser().parse_file(path, None)
        self.assertEqual(str(unitblock.variables), vars)

    def test_hierarchical_vars(self) -> None:
        vars = "[grades:None:[Jane Doe:'10', Jim Doe:'6'], default:None:[zabbix:None:[database:None:[password:''], test:None:[name:'something']]]]"
        self.__test_parse_vars("tests/hierarchical/chef/vars.rb", vars)


if __name__ == "__main__":
    unittest.main()
