import inspect
from typing import Any, Callable, ForwardRef, get_args, get_type_hints


def compare(a: Any, b: Any, strict: bool) -> bool:
    """
    Compare provided values using strict (`is`) or non strict (`==`) comparison.
    """
    return a is b if strict else a == b


def find_callable_param_annotation_by_default(
    callable: Callable, default_value: Any, strict: bool = True
) -> Any:
    """
    Inspect callable signature and finds a parameter that corresponds to provided
    default value. Resolves type annotation

    Args:
        callable: Callable to be inspected
        default_value: Value to be compared with callable signature defaults
        strict: How to perform the search. If `True` (default), will use `is`
            comparison. Else uses ordinary equality.

    Raises:
        `KeyError`: If there is no annotation present on the parameter
        `TypeError`: if some type object is not supported
        `ValueError`: if no signature can be retrieved
        `Exception`: When evaluation of postponed annotations cant be performed
        `NameError`: When get_type_hints() cannot resolve forward references
        `LookupError`: If provided default value not found. Note: Lookup error
            is raised at the end of every case. Catch it as the last.

    """

    # eval str can raise any kind of exception
    sig = inspect.signature(callable)

    # Resolve forward refs using get_type_hints
    type_hints = get_type_hints(callable)

    for param_name, param in sig.parameters.items():
        if compare(param.default, default_value, strict):
            # Get annotation resolved
            return type_hints[param_name]

    raise LookupError(f"{default_value=} not found in {sig=}")


def contains_forward_refs(type_: Any) -> bool:
    """
    This function returns `True` if provided type is a string or forward ref instance,
    or any of its type parameters contains forward reference or is a string instance
    """
    if isinstance(type_, str) or isinstance(type_, ForwardRef):
        return True

    args = get_args(type_)

    for arg in args:
        if contains_forward_refs(arg):
            return True

    return False
