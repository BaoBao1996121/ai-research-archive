"""Simple farewell module."""


def farewell(name: str) -> str:
    """Return a farewell message.

    Args:
        name: The person's name.

    Returns:
        A farewell string.
    """
    return f"Goodbye, {name}!"


if __name__ == "__main__":
    print(farewell("World"))
