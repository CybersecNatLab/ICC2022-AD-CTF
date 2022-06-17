import os
import authlib

base_path = "users"

def add_user(username, password):
    try:
        secret = authlib.get_secret(password)
        with open(os.path.join(base_path, username), "x") as f:
            f.write(secret)
        return True
    except FileExistsError:
        return False

def retrieve_secret_by_username(username):
    try:
        with open(os.path.join(base_path, username), "r") as f:
            return f.read().strip()
        return True
    except FileNotFoundError:
        return False
