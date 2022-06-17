from pwn import *
import authlib
import sys
import string

context.log_level = "error"

PORT = 1234

SERVICES = {
    "ExamNotes": "1",
    "EncryptedNotes": "2",
    "ExamPortal": "3"
}

banner = """
==============================================
|                                            |
|                   .odbo.                   |
|               .od88888888bo.               |
|           .od8888888888888888bo.           |
|       .od888888888888888888888888bo.       |
|    od88888888888888888888888888888888bo    |
|     `~888888888888888888888888888888~'     |
|        `~888888888888888888888888~'|       |
|           `~888888888888888888~'   |       |
|             |`~888888888888~'|     |       |
|             \   `~888888~'   /     A       |
|              `-_   `~~'   _-'      H       |
|                 `--____--'                 |
|                                            |
|        ooo,    .---.                       |
|       o`  o   /    |\________________      |
|      o`   'oooo()  | ________   _   _)     |
|      `oo   o` \    |/        | | | |       |
|        `ooo'   `---'         "-" |_|       |
|                                            |
==============================================
"""

ALPH = string.ascii_letters + string.digits

if len(sys.argv) != 2:
    print('Usage: python3 client.py <server ip>')
    exit(1)

def validate_string(s):
    return all([c in ALPH for c in s]) and len(s) > 7 and len(s) < 65

class Client():
    def __init__(self, server_ip, username, password, service):
        self.server_addr = server_ip
        self.server_port = PORT
        self.username = username
        self.password = password
        self.service = service
        self.auth_token = None
        self.shared_key = None

    def open_connection(self):
        s = remote(self.server_addr, self.server_port)
        assert s.recvline(False) == b"HELLO"
        s.sendline(b"HELLO")
        assert s.recvline(False) == b"OK"
        return s

    def register(self):
        s = self.open_connection()
        s.sendline(b"REG")
        assert s.recvline(False) == b"OK"
        s.sendline(self.username.encode())
        resp = s.recvline(False)
        if resp != b"OK":
            return False
        s.sendline(self.password.encode())
        resp = s.recvline(False)
        s.close()
        if resp != b"OK":
            return False
        return True

    def login(self):
        auth = authlib.AuthClient(self.username, self.password)
        initial_values = auth.get_starting_values()
        s = self.open_connection()
        s.sendline(b"AUTH")
        assert s.recvline(False) == b"OK"
        s.sendline(self.username.encode())
        resp = s.recvline(False)
        if resp != b"OK":
            return False
        s.sendline(initial_values.encode())
        intermediate_values = s.recvline(False).decode()
        final_values = auth.get_final_values(intermediate_values)
        s.sendline(final_values.encode())
        self.auth_token = s.recvline(False).decode()
        self.shared_key = auth.get_shared_key()
        s.close()
        return True

    def get_token(self):
        token_client = authlib.TicketClient(self.username, self.service, self.auth_token, self.shared_key)
        user_token = token_client.get_user_token()
        s = self.open_connection()
        s.sendline(b"TOKEN")
        assert s.recvline(False) == b"OK"
        s.sendline(user_token.encode() + b"." + self.auth_token.encode())
        key_token, service_token = s.recvline(False).decode().split(".")
        s.close()
        return token_client.finalize_token(key_token, service_token)

try:
    print()
    print(banner)
    print()
    print("Welcome to the CyberUni™ authentication system, what do you want to do?")
    print("1. Register a new account")
    print("2. Obtain a login token for a service")
    print("0. Exit")

    choice = int(input("> "))
    if choice not in [0,1,2]:
        print("I don't know that command...")
    elif choice == 0:
        print("Bye!")
    else:
        service_number = None
        username = input("Username: ").strip()
        assert validate_string(username), "username must contain at least 8 characters and at most 64. Only letters and digits allowed!"
        password = input("Password: ").strip()
        assert validate_string(password), "password must contain at least 8 characters and at most 64. Only letters and digits allowed!"
        if choice == 2:
            print()
            print("Available services:")

            for s in SERVICES:
                print(f"- {s}")

            print()
            service = input("Choose the service you want to connect to: ").strip()
            assert service in SERVICES, "service not recognized."
            service_number = SERVICES[service]

        c = Client(sys.argv[1], username, password, service_number)

        if choice == 1:
            c.register()
        else:
            resp = c.login()
            if resp:
                token = c.get_token()
                print(f"You can login to the service {service} using the token {token}")
            else:
                print("Login failed")

except Exception as e:
    print(f"It seems that something bad just happened: {e}")
    print("Please try again later!")
