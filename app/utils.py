from passlib.context import CryptContext
import hashlib

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Once a password is hashed, it cannot be traced back to the original password
def verify_password(plain_password: str, hashed_password: str) -> str:
    return hash_password(plain_password) == hashed_password