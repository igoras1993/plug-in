from plug_in import plug
from impl import InStoreSession, MemoryStore
from base import Store, Session
from plug_in import get_root_config


def configure():
    get_root_config().init_root_registry(
        [
            plug(InStoreSession).into(Session).via_provider("factory"),
            plug(MemoryStore).into(Store).via_provider("lazy"),
        ]
    )
