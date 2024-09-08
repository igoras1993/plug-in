from typing import Protocol


class Session(Protocol):
    def get_data(self, id: str) -> str: ...


class Store(Protocol):
    def fetch[T](self, entity_type: type[T], id: str) -> T: ...
