from ruamel.yaml.tokens import Token
from typing import List, Union, Optional, Any
from ruamel.yaml.error import StreamMark

RecursiveTokenList = List[Union[Token, "RecursiveTokenList", None]]

class Node:
    comment: Optional[RecursiveTokenList]
    value: Any
    start_mark: StreamMark
    end_mark: StreamMark

class ScalarNode(Node): ...
class MappingNode(Node): ...
class SequenceNode(Node): ...
class CollectionNode(Node): ...
