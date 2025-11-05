from collections.abc import Iterable
from typing import Any, Generic, TypeVar

from pydantic._internal._schema_generation_shared import CallbackGetCoreSchemaHandler

T = TypeVar("T")


class DynamicValue(Generic[T]):
    """
    DynamicValue class that represents a value that can be dynamically generated.

    This class is used to indicate that a value should be generated at runtime,
    rather than being statically defined in the configuration.

    Type Parameters:
        T: The type of the value held by this DynamicValue instance.
    """

    def __init__(self, values: Iterable[T]) -> None:
        """Initialize a new DynamicValue instance."""
        self.values: Iterable[T] = values

    def __repr__(self) -> str:
        """Return a string representation of the DynamicValue."""
        return f"DynamicValue({self.values})"

    def __iter__(self) -> Iterable[T]:
        """Return an iterator over the values."""
        return iter(self.values)

    def __get_pydantic_core_schema__(cls, handler: CallbackGetCoreSchemaHandler) -> Any:
        """Pydantic v2 core schema generation hook."""
        print("Generating pydantic core schema for DynamicValue")

        schema = handler.generate_schema(T)

        print("Generated schema:", schema)
        return schema
