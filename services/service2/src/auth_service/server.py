import authlib
import user_handlers
import string
import os
import sys

AUTH_KEY = os.environ["MasterKey"]
SERVICE_KEYS = [os.environ["ExamNotesKey"], os.environ["EncryptedNotesKey"], os.environ["ExamPortalKey"]]

ALPH = string.ascii_letters + string.digits

available_commands = ["AUTH", "TOKEN", "REG"]

def validate_string(s):
    return all([c in ALPH for c in s]) and len(s) > 7 and len(s) < 65

class Server():
    def __init__(self):
        pass

    def handle_ack(self):
        print("HELLO")
        assert input().strip() == "HELLO"
        print("OK")

    def get_user_choice(self):
        req = input().strip()
        if req in available_commands:
            print("OK")
            return req
        print("BAD")
        return

    def handle_registration(self):
        username = input().strip()
        if not validate_string(username):
            print("BAD_USER")
            return

        print("OK")
        password = input().strip()

        if not validate_string(password):
            print("BAD_PSW")
            return

        chk = user_handlers.add_user(username, password)

        if chk:
            print("OK")
        else:
            print("USER_EXISTS")


    def handle_login(self):
        username = input().strip()
        h = user_handlers.retrieve_secret_by_username(username)

        if h is None:
            return "BAD"

        auth = authlib.AuthService(username, h, AUTH_KEY)

        if not validate_string(username):
            return "BAD"
        print("OK")

        initial_values = input().strip()
        intermediate_values = auth.get_values(initial_values)
        print(intermediate_values)
        final_values = input().strip()

        return auth.finalize_token(final_values)

    def handle_token(self):
        ticket_service = authlib.TicketService(AUTH_KEY, SERVICE_KEYS)
        user_token, auth_token = input().strip().split(".")

        key_token, service_token = ticket_service.get_service_tokens(user_token, auth_token)
        print(key_token + "." + service_token)


try:
    s = Server()

    s.handle_ack()
    choice = s.get_user_choice()

    if choice == "AUTH":
        auth_token = s.handle_login()
        print(auth_token)
    elif choice == "TOKEN":
        s.handle_token()
    elif choice == "REG":
        s.handle_registration()
except Exception as e:
    print(e, file=sys.stderr)
    print("BAD")
