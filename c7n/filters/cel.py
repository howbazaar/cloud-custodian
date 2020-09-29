from typing import Iterator, cast

from celpy import celtypes


def aws_tag(
    resource: celtypes.MapType, target: celtypes.StringType
) -> celtypes.Value:
    """
    Most of the following comment is wrong.

    The C7N shorthand ``tag:Name`` doesn't translate well to CEL. It extracts a single value
    from a sequence of objects with a ``{"Key": x, "Value": y}`` structure; specifically,
    the value for ``y`` when ``x == "Name"``.

    This function locate a particular "Key": target within a list of {"Key": x, "Value", y} items,
    returning the y value if one is found, null otherwise.

    In effect, the ``tag(key)``    function::

        tag("Name")

    is somewhat like::

        resource["Tags"].filter(x, x["Key"] == "Name")[0]["Value"]

    But the ``key()`` function doesn't raise an exception if the key is not found,
    instead it returns None.

    We might want to generalize this into a ``first()`` reduction macro.
    ``resource["Tags"].first(x, x["Key"] == "Name" ? x["Value"] : null, null)``
    This macro returns the first non-null value or the default (which can be ``null``.)
    """
    key = celtypes.StringType("Key")
    value = celtypes.StringType("Value")

    source = resource.get("Tags", [])

    matches: Iterator[celtypes.Value] = (
        item
        for item in source
        if cast(celtypes.StringType, cast(celtypes.MapType, item).get(key))
        == target  # noqa: W503
    )
    try:
        return cast(celtypes.MapType, next(matches)).get(value)
    except StopIteration:
        return None
