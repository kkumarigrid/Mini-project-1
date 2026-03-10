import bcrypt
from db import db

class Auth:

    def signup(self, username: str, password: str) -> tuple:
        if not username or not username.strip():
            return False, "Username cannot be empty."
        if len(username.strip()) < 4:
            return False, "Username must be at least 4 characters."
        if not password or len(password) < 3:
            return False, "Password must be at least 3 characters."

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try:
            with db.get_cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username.strip(), hashed)
                )
            return True, "Account created! You can now log in."
        except Exception:
            return False, "Username already taken."

    def login(self, username: str, password: str) -> tuple:
        if not username or not password:
            return None, "Please enter both username and password."

        with db.get_cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE username = %s", (username.strip(),)
            )
            user = cur.fetchone()

        if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
            return dict(user), f"Welcome back, {username}!"

        return None, "Invalid username or password."

_auth = Auth()

def signup(username, password):
    return _auth.signup(username, password)

def login(username, password):
    return _auth.login(username, password)