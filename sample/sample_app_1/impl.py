from dataclasses import dataclass
from base import Store
from entities import User
from plug_in import Hosted, manage


@manage()
@dataclass
class InStoreSession:
    store: Store = Hosted()

    def get_data(self, id: str) -> str:
        return self.store.fetch(User, id).session_data or ""


class MemoryStore:
    _mem = [User("user1", "1", 10, "some_data")]

    def fetch[T](self, entity_type: type[T], id: str) -> T:

        for item in self._mem:
            if isinstance(item, entity_type) and item.id == id:
                return item

        raise LookupError()
