from entities import User
from base import Store, Session
from plug_in import manage, Hosted


@manage()
def get_user(id: str, store: Store = Hosted()) -> User:
    return store.fetch(User, id)


@manage()
def get_user_session_data(id: str, session: Session = Hosted()) -> str:
    return session.get_data(id)
