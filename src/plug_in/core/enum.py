from enum import StrEnum


class PluginPolicy(StrEnum):
    DIRECT = "DIRECT"
    LAZY = "LAZY"
    FACTORY = "FACTORY"
