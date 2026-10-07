import hashlib
import hmac
import os

ITERATIONS=600000

def hash_password(password):
    if not isinstance(password,str):
        raise TypeError("password must be str")
    salt=os.urandom(16)
    digest=hashlib.pbkdf2_hmac("sha256",password.encode("utf-8"),salt,ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"

def verify_password(password,stored_hash):
    try:
        algorithm,iterations,salt_hex,digest_hex=stored_hash.split("$")
        if algorithm!="pbkdf2_sha256":
            return False
        actual=hashlib.pbkdf2_hmac(
            "sha256",password.encode("utf-8"),bytes.fromhex(salt_hex),int(iterations)
        )
        return hmac.compare_digest(actual,bytes.fromhex(digest_hex))
    except (ValueError,TypeError,AttributeError):
        return False
