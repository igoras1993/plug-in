from enum import StrEnum


class PluginPolicy(StrEnum):
    DIRECT = "DIRECT"
    LAZY = "LAZY"
    FACTORY = "FACTORY"
    LAZY_ASYNC = "LAZY_ASYNC"
    FACTORY_ASYNC = "FACTORY_ASYNC"
