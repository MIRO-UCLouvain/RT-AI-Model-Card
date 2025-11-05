"""Module for manipulating collections."""
from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


def insert_after(
    odict: Mapping[str, object],
    new_key: str,
    new_value: object,
    after_key: str,
) -> OrderedDict[str, object]:
    """
    Insert a new key/value pair into an OrderedDict-like mapping after a specified key.

    :param odict: The original mapping to modify.
    :type odict: Mapping[str, object]
    :param new_key: The key to insert.
    :type new_key: str
    :param new_value: The value to insert.
    :type new_value: object
    :param after_key: The key after which to insert the new key/value pair.
    :type after_key: str
    :return: The modified mapping with the new key/value pair inserted.
    :rtype: OrderedDict[str, object]
    """  # noqa: E501
    if not odict:
        return OrderedDict({new_key: new_value})

    new_items: list[tuple[str, object]] = []
    for key, value in odict.items():
        new_items.append((key, value))
        if key == after_key:
            new_items.append((new_key, new_value))
    return OrderedDict(new_items)


def insert_dict_after(
    base_dict: Mapping[str, object],
    insert_dict: Mapping[str, object],
    after_key: str,
) -> OrderedDict[str, object]:
    """
    Insert all key/value pairs from one dict after a given key in another.

    :param base_dict: Base mapping (order preserved).
    :type base_dict: Mapping[str, object]
    :param insert_dict: Dictionary of key/value pairs to insert.
    :type insert_dict: Mapping[str, object]
    :param after_key: Key in base_dict after which insert_dict is inserted.
    :type after_key: str
    :return: A new OrderedDict with insert_dict merged in after after_key.
    :rtype: OrderedDict[str, object]
    """
    new_items: list[tuple[str, object]] = []
    for key, value in base_dict.items():
        new_items.append((key, value))
        if key == after_key:
            new_items.extend(insert_dict.items())
    return OrderedDict(new_items)
