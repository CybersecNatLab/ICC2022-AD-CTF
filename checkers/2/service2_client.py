import authlib
from pwn import *

context.log_level = "error"

class Client():
    def __init__(self, server_ip, server_port, username, password, service):
        self.server_addr = server_ip
        self.server_port = server_port
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
