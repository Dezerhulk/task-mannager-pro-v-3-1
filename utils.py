import re


def normalize_spaces(s: str) -> str:
    """Collapse all whitespace to single spaces and trim ends."""
    if s is None:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def to_slug(s: str) -> str:
    """Convert a string to a lowercase URL-friendly slug.

    Examples:
    - "Python___is   Cool!!" -> "python-is-cool"
    - "Hello World!!!" -> "hello-world"
    """
    if s is None:
        return ""
    s = normalize_spaces(s)
    s = s.lower()
    # replace any sequence of non-alphanumeric characters with a space
    s = re.sub(r"[^a-z0-9]+", " ", s)
    # convert spaces to hyphens
    s = re.sub(r"[\s]+", "-", s)
    # collapse multiple hyphens
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


if __name__ == "__main__":
    # Test normalize_spaces
    test1 = "  a   b  "
    result1 = normalize_spaces(test1)
    print(f'normalize_spaces("{test1}") → "{result1}"')
    assert result1 == "a b", f"Expected 'a b', got '{result1}'"

    # Test to_slug
    test2 = "Python___is   Cool!!"
    result2 = to_slug(test2)
    print(f'to_slug("{test2}") → "{result2}"')
    assert result2 == "python-is-cool", f"Expected 'python-is-cool', got '{result2}'"

    test3 = "Hello World!!!"
    result3 = to_slug(test3)
    print(f'to_slug("{test3}") → "{result3}"')
    assert result3 == "hello-world", f"Expected 'hello-world', got '{result3}'"

    print("✅ All tests passed!")