from collections.abc import Callable
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any


class RunWrapper:
    """Base class for run wrappers."""

    run_wrappers: list[Any] = []

    def __init_subclass__(cls: type["RunWrapper"], **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.run_wrappers.extend(
            getattr(cls, name)
            for name in dir(cls)
            if hasattr(getattr(cls, name), "_is_run_wrapper")
        )

    @asynccontextmanager
    async def wrapped(self):
        async with AsyncExitStack() as stack:
            # Enter all wrappers in order
            for wrapper in self.run_wrappers:
                await stack.enter_async_context(wrapper(self))

            yield


def on_run(cls_or_func: type[RunWrapper] | Callable[..., Any] | None = None) -> Callable[..., Any]:
    """Decorator to mark a function as a run wrapper for Strategy."""
    cls_type: type[RunWrapper] | None = None

    def func_wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        func = asynccontextmanager(func)
        func.__setattr__("_is_run_wrapper", True)

        if cls_type:
            cls_type.run_wrappers.append(func)

        return func

    if isinstance(cls_or_func, type) and issubclass(cls_or_func, RunWrapper):
        cls_type = cls_or_func
        return func_wrapper
    elif callable(cls_or_func):
        return func_wrapper(cls_or_func)
    else:
        raise TypeError("on_run must be used with a RunWrapper subclass or a function")
