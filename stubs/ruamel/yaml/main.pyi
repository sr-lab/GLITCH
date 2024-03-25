from ruamel.yaml.nodes import Node
from typing import TextIO

class YAML:
    def compose(self, stream: str | TextIO) -> Node | None: ...
