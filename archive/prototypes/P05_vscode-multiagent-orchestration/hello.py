"""Simple greeting module."""


def greet(name: str) -> str:
    """Return a greeting message.

    Args:
        name: The person's name.

    Returns:
        A greeting string.
    """
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(greet("World"))
