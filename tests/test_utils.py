import string

from app.utils import generate_code


def test_generate_code_length_and_alphabet():
    code = generate_code(10)
    allowed = set(string.ascii_letters + string.digits)

    assert len(code) == 10
    assert set(code) <= allowed
