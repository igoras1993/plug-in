from typing import Callable


type Manageable[R, **Ps] = Callable[Ps, R]
