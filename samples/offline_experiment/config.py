from collections.abc import Generator

from pydantic import BaseModel

from spearmint.core import DynamicValue


class MyConfig(BaseModel):
    id: int


def generate_id() -> Generator[int, None, None]:
    """Generate a list of IDs."""
    ids = [10, 20, 30]
    yield from ids


my_dynamic_list_config = {
    "id": DynamicValue([10, 20, 30]),
}

my_dynamic_range_config = {
    "id": DynamicValue(range(10, 40, 10)),
}

my_dynamic_generator_config = {
    "id": DynamicValue(generate_id()),
}
