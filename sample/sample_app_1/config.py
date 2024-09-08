from plug_in import BootstrapWizard, plug
from impl import InStoreSession, MemoryStore
from base import Store, Session


def configure():
    BootstrapWizard().configure_root_registry(
        [
            plug(InStoreSession).into(Session).via_provider("factory"),
            plug(MemoryStore).into(Store).via_provider("lazy"),
        ]
    )
