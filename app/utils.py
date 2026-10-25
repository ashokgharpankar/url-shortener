import secrets
import string

ALPHABET = string.ascii_letters + string.digits  # base62


def generate_code(length: int) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
