 import re


def validate_not_empty(s: str) -> str:
    """Strip whitespace and ensure string is not empty.

    Args:
        s: input string

    Returns:
        cleaned string

    Raises:
        ValueError: if resulting string is empty.
    """
    value = s.strip()
    if not value:
        raise ValueError("Пустая строка")
    return value


def validate_int_range(x: int, min_v: int, max_v: int) -> int:
    """Ensure an integer lies within a closed interval.

    Args:
        x: value to check
        min_v: lower bound (inclusive)
        max_v: upper bound (inclusive)

    Returns:
        the original x if it lies within range

    Raises:
        ValueError: if x is outside of [min_v, max_v]
    """
    if not (min_v <= x <= max_v):
        raise ValueError(f"Число должно быть в диапазоне {min_v}..{max_v}")
    return x


def validate_username(name: str) -> str:
    """Validate a username according to project rules.

    Rules:
    * length must be between 3 and 20 characters
    * only Latin letters, digits and underscore are allowed
    * must not start with a digit

    Args:
        name: candidate username

    Returns:
        the stripped username

    Raises:
        ValueError: on any violation of the rules
    """
    name = name.strip()
    if not (3 <= len(name) <= 20):
        raise ValueError("Имя пользователя должно содержать от 3 до 20 символов")

    # first character must be a letter or underscore, subsequent may be letters, digits or underscore
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        raise ValueError(
            "Имя пользователя может содержать только латиницу, цифры и '_' и не начинаться с цифры"
        )
    return name
