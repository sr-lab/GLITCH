from typing import Dict


class State:
    def __init__(self) -> None:
        self.attrs: Dict[str, str] = {}

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, State):
            return False
        return self.attrs == value.attrs

    def __repr__(self) -> str:
        return str(self.attrs)


class FileSystemState:
    def __init__(self) -> None:
        self.state: Dict[str, State] = {}

    def copy(self):
        fs = FileSystemState()
        fs.state = self.state.copy()
        return fs
