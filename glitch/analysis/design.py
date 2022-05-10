import json
import configparser
from glitch.analysis.rules import Error, RuleVisitor

from glitch.repr.inter import *

class DesignVisitor(RuleVisitor):
    @staticmethod
    def get_name() -> str:
        return "design"

    def config(self, config_path: str):
        config = configparser.ConfigParser()
        config.read(config_path)
        DesignVisitor.__EXEC = json.loads(config['design']['exec_atomic_units'])

    def check_dependency(self, d: Dependency, file: str) -> list[Error]:
        pass

    def check_attribute(self, a: Attribute, file: str) -> list[Error]:
        pass

    def check_variable(self, v: Variable, file: str) -> list[Error]:
        pass

    def check_comment(self, c: Comment, file: str) -> list[Error]:
        pass