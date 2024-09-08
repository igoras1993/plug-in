from dataclasses import dataclass


@dataclass
class User:
    id: str
    name: str
    strength: int
    session_data: str | None = None
