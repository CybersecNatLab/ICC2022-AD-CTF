#!/usr/bin/env python3

# Do not make modification to checklib.py (except for debug), it can be replaced at any time
import checklib
import requests
import random
import string
from hashlib import sha256
import json
import os
import functools
from bs4 import BeautifulSoup
import errno
os.environ["PWNLIB_NOTERM"] = "1"
from service2_client import Client as AuthClient

data = checklib.get_data()
action = data['action']
rd = data['round']
team_id = data['teamId']
service_name = "ExamPortal"

port = 1237
auth_port = 1234
team_ip = f"10.60.{team_id}.1"
team_addr = f"http://{team_ip}:{port}"


# Create directory to store round data.
data_dir = 'data'
try:
    os.makedirs(data_dir)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise


# Read stored data for team-round
def read_round_data():
    try:
        fl = sha256(data['flag'].encode()).hexdigest()
        with open(f'{data_dir}/{team_id}-{fl}.json', 'r') as f:
            raw = f.read()
            return json.loads(raw)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}


# Store data for team-round
def store_round_data(d):
    raw = json.dumps(d)
    fl = sha256(data['flag'].encode()).hexdigest()

    with open(f'{data_dir}/{team_id}-{fl}.json', 'w') as f:
        f.write(raw)


def random_string(min, max):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(random.randint(min, max)))


# Auth stuff
def get_random_creds():
    username = random_string(8, 24)
    password = random_string(8, 24)
    return username, password


def register_random_user():
    username, password = get_random_creds()
    register_user(username, password)
    return username, password


def register_user(username, password):
    try:
        c = AuthClient(team_ip, auth_port, username, password, "3")
        c.register()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      'Can\'t register user on auth service', str(e))


def get_token(username, password):
    try:
        c = AuthClient(team_ip, auth_port, username, password, "3")
        c.login()
        token = c.get_token()
        return token
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      'Can\'t get a token from auth service', str(e))


def get_sess():
    s = requests.Session()
    s.request = functools.partial(s.request, timeout=5)
    with open('user_agents.txt', 'r') as f:
        ua_list = f.readlines()
    s.headers.update({'User-Agent': random.choice(ua_list)[:-1]})
    return s


def do_login(sess, token, tfa=None):
    try:
        r = sess.post(team_addr+"/login.php",
                      data={"token": token, "2fa": tfa})
        if "Token verification failed" in r.text:
            checklib.quit(checklib.Status.DOWN, 'Token decoding failed',
                          f"do_login {team_addr}/login.php (token={token}, 2fa={tfa}): {r.text}")
        if "Authentication failed!" in r.text:
            checklib.quit(checklib.Status.DOWN, 'Can\'t login',
                          f"do_login {team_addr}/login.php (token={token}, 2fa={tfa}): {r.text}")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Login failed',
                      f"do_login (token={token}, tfa={tfa}): {e}")


# Check SLA
def check_sla():

    sess = get_sess()
    username, password = register_random_user()
    token = get_token(username, password)
    tfa = None
    if random.randrange(2) == 0:
        tfa = random_string(10, 10)

    try:
        do_login(sess, token, tfa)

        r = sess.get(team_addr)
        if username not in r.text:
            checklib.quit(checklib.Status.DOWN, 'Can\'t login',
                          f"do_login {team_addr}/index.php : {r.text}")

        r = sess.get(team_addr+"/exam_list.php")
        if r.status_code != 200:
            checklib.quit(checklib.Status.DOWN, 'Can\'t list exams',
                          f"check_sla {team_addr}/exam_list.php : {r.status_code}\n{r.text}")

        if tfa is not None:
            sess = get_sess()
            do_login(sess, token, tfa)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Login failed', f"check_sla : {e}")

    checklib.quit(checklib.Status.OK, 'OK')


QQ = [
    {"question": "What is the answer?", "answers": [
        "42", "The onion", "Yes", "answer"]},
    {"question": "Is pwn funny?", "answers": ["no", "no", "no", "no"]},
    {"question": "What's the best post-quantum candidate?",
        "answers": ["NTRU", "McEliece", "SIKE", "Rainbow"]},
    {"question": "What's the best pwning tool?", "answers": [
        "gef", "AFL++", "pwntools", "calc.exe"]},
    {"question": "This website is vulnerable to:", "answers": [
        "SQLi", "XSS", "CSRF", "Social engineering"]},
    {"question": "What's your favourite CVE?", "answers": [
        "CVE-2021-44228", "CVE-2022-0778", "CVE-2021-26855", "CVE-2014-0160"]},
    {"question": "Which one of the following describes spam?", "answers": ["Gathering information about a person or organisation without their knowledge",
                                                                           "Performing an unauthorised, usually malicious, action such as erasing files", "Putting unnecessary load on the network by making copies of files", "Sending unwanted bulk messages"]},
    {"question": "Which one of the following describes a computer hacker?", "answers": ["A skilled programmer who uses authorised access to exploit information available on a computer",
                                                                                        "A skilled programmer who secretly invades computers without authorisation", "A skilled programmer who writes programs to train new employees", "A skilled programmer who helps in the installation of new software for an organisation"]},
    {"question": "Which one of the following should be used to change your password?", "answers": [
        "Control Panel", "Anti-virus software", "Windows Firewall", "Internet Explorer"]},
    {"question": "Which one of the following would be considered the BEST way to store a PIN number?", "answers": [
        "Keep a written note of it with you bank cards", "Store it on your computer", "Memorise it", "Keep a written note of it in your office drawer"]},
    {"question": "What information do you need to set up a wireless access point?",
        "answers": ["SSID", "MAC address", "IP address", "ARP"]},
    {"question": "Which of the following is a password hashing algorithm?",
        "answers": ["AES", "MD4", "PGP", "3DES"]},
    {"question": "Which of the following is a private search engine?",
        "answers": ["Bing", "Google", "Duckduckgo", "Yahoo"]},
    {"question": "Which cybersecurity principle is most important when attempting to trace the source of malicious activity?",
        "answers": ["Availability", "Integrity", "Nonrepudiation", "Confidentiality"]},
    {"question": "Updates in cloud-computing environments can be rolled out quickly because the environment is:",
        "answers": ["Homogeneous", "Distributed", "Diversified", "Secure"]},
    {"question": "The attack mechanism directed against a system is commonly called a(n):", "answers": [
        "Exploit", "Vulnerability", "Payload", "Attack vector"]},
    {"question": "If security is a real concern on your network, what length do most experts recommend as the minimum for password length?",
        "answers": ["10", "9", "8", "6"]},
    {"question": "Which of the following is an asymmetric algorithm based on calculating logarithms?",
        "answers": ["ECC", "Diffie-Hellman", "El Gamal", "RSA"]}
]
NAMES = ["Machine learning", "Quantum cryptography", "Biometrics", "Network Security", "Law and data", "Digital forensics", "Mobile and IOT security", "Smart contracts hacking", "Wireless networks",
         "Big data computing", "APT monitoring", "Cyber threat analysis", "Advanced reverse engineering", "Financial Accounting", "Virtualization & Cloud Security", "Ethical Hacking", "Malware Analysis"]


def create_random_exam():
    name = random.choice(NAMES) + " " + str(random.randint(1, 4))
    questions = random.sample(QQ, 10)
    correct = random.choices(["A", "B", "C", "D"], k=10)
    return name, questions, correct


def check_correct_in_page(html, answers, correct):
    # print(html)
    soup = BeautifulSoup(html, 'html.parser')
    html_ans = soup.find_all("ul")[1:]
    assert len(html_ans) == len(answers)
    for i, x in enumerate(html_ans):
        cur_ans = x.find_all("li")
        # print(cur_ans)
        assert len(cur_ans) == 4
        for j, y in enumerate(cur_ans):
            val = y.text.strip()
            assert val == answers[i][j]
            if ["A", "B", "C", "D"].index(correct[i]) == j:
                exp_class = "bg-success"
            else:
                exp_class = "bg-danger"
            assert exp_class == y["class"][2]


# Put the flag using the flag as the seed for random stuff
def put_flag():
    flag = data['flag']

    sess = get_sess()
    username, password = register_random_user()
    token = get_token(username, password)
    tfa = random_string(10, 10)
    do_login(sess, token, tfa)

    name, questions, correct = create_random_exam()

    exam = {}
    exam["name"] = name
    exam["prize"] = flag
    for i in range(10):
        exam[f"question_{i}"] = questions[i]["question"]
        exam[f"correct_{i}"] = correct[i]
        assert len(questions[i]["answers"]) == 4
        for j in range(4):
            exam[f"answer_{i}_{j}"] = questions[i]["answers"][j]
    try:
        r = sess.post(team_addr+"/exam_create.php", data=exam)
        if r.status_code != 200:
            checklib.quit(checklib.Status.DOWN, 'Can\'t create exam',
                          f"put_flag {team_addr}/exam_create.php (exam={exam}): {r.status_code}\n{r.text}")
        id = r.url.split("=")[1]
        if "Unauthorized" in r.text or "No such exam" in r.text:
            checklib.quit(checklib.Status.DOWN, 'Can\'t view exam',
                          f"put_flag {team_addr}/exam_create.php : {r.status_code}\n{r.text}")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Error in creating exam', str(e))

    store_round_data({"creds": {"username": username, "password": password, "tfa": tfa}, "exam": {
                     "id": id, "name": name, "questions": questions, "correct": correct}})

    try:
        check_correct_in_page(r.text, [x["answers"]
                              for x in questions], correct)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Malformed exam', str(e))

    checklib.post_flag_id(service_name, team_ip, id)

    # If OK
    checklib.quit(checklib.Status.OK, 'OK')


def get_flag_view_exam(exam, creds):
    id, name, questions, correct = exam["id"], exam["name"], exam["questions"], exam["correct"]
    token, tfa = creds
    sess = get_sess()
    do_login(sess, token, tfa)
    r = sess.get(team_addr+"/exam_view.php", params={"id": id})
    if "Unauthorized" in r.text or "No such exam" in r.text:
        checklib.quit(checklib.Status.DOWN, 'Can\'t view exam',
                      f"get_flag_view_exam {team_addr}/exam_view.php (id={id}): {r.status_code}\n{r.text}")
    try:
        check_correct_in_page(r.text, [x["answers"]
                              for x in questions], correct)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Malformed exam', str(e))


def get_flag_solve_exam(exam, creds):
    id, name, questions, correct = exam["id"], exam["name"], exam["questions"], exam["correct"]
    username, password = creds
    token = get_token(username, password)
    sess = get_sess()
    do_login(sess, token, None)
    exam_ans = {"id": id, "answers": correct}
    r = sess.post(team_addr+"/exam_submit.php", json=exam_ans)
    if data["flag"] not in r.json()["msg"]:
        checklib.quit(checklib.Status.DOWN, 'Can\'t solve exam',
                      f"get_flag_solve_exam {team_addr}/exam_submit.php (exam_ans={exam_ans}): {r.status_code}\n{r.text}")


# Check if the flag still exists, use the flag as the seed for random stuff as for put flag
def get_flag():
    round_data = read_round_data()
    username = round_data["creds"]["username"]
    password = round_data["creds"]["password"]
    tfa = round_data["creds"]["tfa"]
    exam = round_data["exam"]
    check = random.randrange(2)

    try:
        if check == 0:
            token = get_token(username, password)
            get_flag_view_exam(exam, (token, tfa))
        if check == 1:
            u2, p2 = register_random_user()
            get_flag_solve_exam(exam, (u2, p2))
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Get flag failed', str(e))

    # If OK
    checklib.quit(checklib.Status.OK, 'OK')


if __name__ == "__main__":

    if action == checklib.Action.CHECK_SLA.name:
        check_sla()
    elif action == checklib.Action.PUT_FLAG.name:
        put_flag()
    elif action == checklib.Action.GET_FLAG.name:
        get_flag()
