import bcrypt

def hash_password(password: str) -> str:
    """
    Securely hashes a plaintext password using bcrypt.

    Steps:
    1) bcrypt.gensalt() generates a random “salt” (and embeds the cost factor).
    2) bcrypt.hashpw(password, salt) computes the salted hash.
    3) We decode to UTF-8 so it’s a regular Python string for storage.

    Returns:
        A string containing both the salt and hash (e.g. b'$2b$12$...').decode()
    """
    # 1) Generate a random salt (default cost=12)
    salt = bcrypt.gensalt()

    # 2) Compute the salted hash
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

    # 3) Return as a UTF-8 string
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hash.

    Args:
        password: The plaintext password to check.
        hashed:        The stored password hash (string form from hash_password).

    Returns:
        True if the password matches the hash, False otherwise.
    """
    # bcrypt.checkpw requires both args as bytes
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))