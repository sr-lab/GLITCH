from ruamel.yaml.error import StreamMark

class Token:
    start_mark: StreamMark
    end_mark: StreamMark

    @property
    def column(self) -> int: ...

class CommentToken(Token):
    value: str
