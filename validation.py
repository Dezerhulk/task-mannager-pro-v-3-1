import re


class ValidationError(Exception):
    """Base validation error for user data."""
    pass


class FieldError(ValidationError):
    """Raised when a specific field is invalid.

    Attributes:
        field: name of the invalid field
        message: short description of the error
    """

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def validate_user(data: dict) -> dict:
    """Validate a user dict and return cleaned data.

    Raises FieldError for individual field problems and ValidationError
    for other validation issues.
    """
    if not isinstance(data, dict):
        raise ValidationError("user data must be a dict")

    username = data.get("username")
    if not isinstance(username, str) or len(username.strip()) < 3:
        raise FieldError("username", "must be at least 3 characters")

    age = data.get("age")
    if not isinstance(age, int) or not (14 <= age <= 120):
        raise FieldError("age", "must be integer between 14 and 120")

    email = data.get("email", "")
    if not isinstance(email, str) or "@" not in email or not re.search(r"\.[a-zA-Z]{2,}$", email):
        raise FieldError("email", "invalid email")

    # Return normalized/validated dict (could be copy if desired)
    return {"username": username.strip(), "age": age, "email": email}


def validate_registration(data: dict) -> dict:
    """Validate a registration payload.

    Expected fields in *data*:
      * username - see validate_username rules
      * age      - string convertible to int, must be 14..120
      * email    - contains '@' and '.', '@' not at end
      * password - at least 8 chars, one digit, one letter, one special from !@#$%^&*

    Returns a new dict with cleaned values (age as int, strings stripped).
    Raises FieldError for field-specific problems or ValidationError otherwise.
    """
    from validators import validate_username, validate_int_range

    if not isinstance(data, dict):
        raise ValidationError("registration data must be a dict")

    # username
    username = data.get("username", "")
    try:
        username = validate_username(username)
    except ValueError as exc:
        raise FieldError("username", str(exc))

    # age
    age_raw = data.get("age")
    if not isinstance(age_raw, str):
        raise FieldError("age", "must be a string")
    age_raw = age_raw.strip()
    try:
        age_int = int(age_raw)
    except ValueError:
        raise FieldError("age", "must be integer string")
    try:
        age_int = validate_int_range(age_int, 14, 120)
    except ValueError as exc:
        raise FieldError("age", str(exc))

    # email
    email = data.get("email", "")
    if not isinstance(email, str):
        raise FieldError("email", "must be a string")
    email = email.strip()
    if "@" not in email or "." not in email or email.endswith("@"):
        raise FieldError("email", "invalid email")

    # password
    pwd = data.get("password", "")
    if not isinstance(pwd, str):
        raise FieldError("password", "must be a string")
    pwd = pwd.strip()
    if len(pwd) < 8:
        raise FieldError("password", "должен быть не менее 8 символов")
    if not re.search(r"\d", pwd):
        raise FieldError("password", "должен содержать цифру")
    if not re.search(r"[A-Za-z]", pwd):
        raise FieldError("password", "должен содержать букву")
    if not re.search(r"[!@#$%^&*]", pwd):
        raise FieldError("password", "должен содержать спецсимвол !@#$%^&*")

    return {"username": username, "age": age_int, "email": email, "password": pwd}


if __name__ == "__main__":
    samples = [
        {"username": "al", "age": 20, "email": "a@example.com"},
        {"username": "alice", "age": 10, "email": "alice@example.com"},
        {"username": "bob", "age": 30, "email": "bobexample.com"},
        {"username": "carol", "age": 25, "email": "carol@example.org"},
    ]

    for i, s in enumerate(samples, 1):
        try:
            valid = validate_user(s)
            print(f"#{i} OK -> {valid}")
        except FieldError as e:
            print(f"#{i} FieldError: {e.field} -> {e.message}")
        except ValidationError as e:
            print(f"#{i} ValidationError: {e}")

