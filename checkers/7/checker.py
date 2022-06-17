#!/usr/bin/env python3
import base64
import checklib
import errno
import gmpy2
import hashlib
import json
import os
import random
import requests
import string
import time

data = checklib.get_data()
action = data['action']
rd = data['round']
team_id = data['teamId']
service_addr = '10.60.' + team_id + '.1'
service_port = "5000"
service_name = 'Trademark'

SLEEP_MIN_TIME_MS = 500
SLEEP_MAX_TIME_MS = 1500

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
        fl = hashlib.sha256(data['flag'].encode()).hexdigest()
        with open(f'{data_dir}/{team_id}-{fl}.json', 'r') as f:
            raw = f.read()
            return json.loads(raw)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}


# Store data for team-round
def store_round_data(d):
    raw = json.dumps(d)
    fl = hashlib.sha256(data['flag'].encode()).hexdigest()

    with open(f'{data_dir}/{team_id}-{fl}.json', 'w') as f:
        f.write(raw)


def random_string(min, max):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(random.randint(min, max)))


# Check user can register and read profile
def check_sla_user():
    username = random_string(16, 24)
    password = random_string(12, 24)

    # Register user
    r = requests.post(f'http://{service_addr}:{service_port}/api/register',
                      data={'username': username, 'password': password}, timeout=5)
    if r.status_code != 200 and r.status_code != 201:
        checklib.quit(checklib.Status.DOWN, 'Request failure',
                      f'check_sla_user http://{service_addr}/api/register (username={username}, password={password}): {r.status_code}\n{r.text}')

    sessionData = r.json()
    if 'user_id' not in sessionData or not isinstance(sessionData['user_id'], int) or 'session' not in sessionData or not isinstance(sessionData['session'], str):
        checklib.quit(checklib.Status.DOWN, 'Response error',
                      f'check_sla_user http://{service_addr}/api/register (username={username}, password={password}): {r.status_code}\n{r.text}')

    token = 'Bearer ' + \
        base64.b64encode(
            (str(sessionData['user_id'])+':'+sessionData['session']).encode()).decode()

    time.sleep(random.randint(SLEEP_MIN_TIME_MS, SLEEP_MAX_TIME_MS) / 1000)

    # Check profile
    r = requests.get(f'http://{service_addr}:{service_port}/api/users',
                     headers={'Authorization': token}, timeout=5)
    if r.status_code != 200:
        checklib.quit(checklib.Status.DOWN, 'Request failure',
                      f'check_sla_user http://{service_addr}/api/users: {r.status_code}\n{r.text}')

    userData = r.json()
    if 'id' not in userData or not isinstance(userData['id'], int) or 'username' not in userData or not isinstance(userData['username'], str):
        checklib.quit(checklib.Status.DOWN, 'Response error',
                      f'check_sla_user http://{service_addr}/api/users: {r.status_code}\n{r.text}')


# Check SLA
def check_sla():
    slas = [check_sla_user]
    random.shuffle(slas)

    try:
        for sla in slas:
            sla()
    except (requests.ConnectTimeout, requests.ReadTimeout, requests.Timeout) as e:
        checklib.quit(checklib.Status.DOWN, 'Connection timeout', str(e))
    except requests.ConnectionError as e:
        checklib.quit(checklib.Status.DOWN, 'Connection error', str(e))
    except json.decoder.JSONDecodeError as e:
        checklib.quit(checklib.Status.DOWN, 'Response error', str(e))

    checklib.quit(checklib.Status.OK, 'OK')


# Put the flag using the flag as the seed for random stuff
def put_flag():
    flag = data['flag']
    username = random_string(16, 24)
    password = random_string(12, 24)
    product = random_string(16, 24)

    try:
        # Register user
        r = requests.post(f'http://{service_addr}:{service_port}/api/register', data={
                          'username': username, 'password': password}, timeout=5)
        if r.status_code != 200 and r.status_code != 201:
            checklib.quit(checklib.Status.DOWN, 'Request failure',
                          f'put_flag http://{service_addr}/api/register (username={username}, password={password}): {r.status_code}\n{r.text}')

        sessionData = r.json()
        if 'user_id' not in sessionData or not isinstance(sessionData['user_id'], int) or 'session' not in sessionData or not isinstance(sessionData['session'], str):
            checklib.quit(checklib.Status.DOWN, 'Response error',
                          f'put_flag http://{service_addr}/api/register (username={username}, password={password}): {r.status_code}\n{r.text}')

        token = 'Bearer ' + \
            base64.b64encode(
                (str(sessionData['user_id'])+':'+sessionData['session']).encode()).decode()

        time.sleep(random.randint(SLEEP_MIN_TIME_MS, SLEEP_MAX_TIME_MS) / 1000)

        # Create product
        r = requests.post(f'http://{service_addr}:{service_port}/api/products', data={
                          'name': product, 'description': '', 'content': flag}, headers={'Authorization': token}, timeout=15)
        if r.status_code != 200 and r.status_code != 201:
            checklib.quit(checklib.Status.DOWN, 'Request failure',
                          f'put_flag http://{service_addr}/api/products (name={product}): {r.status_code}\n{r.text}')

        productData = r.json()
        if 'id' not in productData or not isinstance(productData['id'], int) or 'keys' not in productData or not isinstance(productData['keys'], list):
            checklib.quit(checklib.Status.DOWN, 'Response error',
                          f'put_flag http://{service_addr}/api/products (name={product}): {r.status_code}\n{r.text}')

        product_id = productData['id']
        keys = []
        for k in productData['keys']:
            if not isinstance(k, str):
                checklib.quit(checklib.Status.DOWN, 'Response error',
                              f'put_flag http://{service_addr}/api/products key not string: {r.status_code}\n{r.text}')
            keys.append(k)
        if len(keys) < 1:
            checklib.quit(checklib.Status.DOWN, 'Response error',
                          f'put_flag http://{service_addr}/api/products key not string: {r.status_code}\n{r.text}')

    except (requests.ConnectTimeout, requests.ReadTimeout, requests.Timeout) as e:
        checklib.quit(checklib.Status.DOWN, 'Connection timeout', str(e))
    except requests.ConnectionError as e:
        checklib.quit(checklib.Status.DOWN, 'Connection error', str(e))
    except json.decoder.JSONDecodeError as e:
        checklib.quit(checklib.Status.DOWN, 'Response error', str(e))

    store_round_data({
        'username': username,
        'password': password,
        'product': product,
        'product_id': product_id,
        'keys': keys,
    })

    checklib.post_flag_id(service_name, service_addr, str(product_id))
    checklib.quit(checklib.Status.OK, 'OK')


# Check if the flag still exists, use the flag as the seed for random stuff as for put flag
def get_flag():
    flag = data['flag']

    storedData = read_round_data()
    if not storedData:
        checklib.quit(checklib.Status.DOWN,
                      'Precondition Failed', 'storedData empty')

    if 'product_id' not in storedData or 'keys' not in storedData:
        checklib.quit(checklib.Status.ERROR, 'Precondition Failed',
                      'storedData invalid: ' + json.dumps(storedData))

    username = random_string(16, 24)
    password = random_string(12, 24)
    product_id = storedData['product_id']
    keys = storedData['keys']

    try:
        # Register user
        r = requests.post(f'http://{service_addr}:{service_port}/api/register', data={
                          'username': username, 'password': password}, timeout=5)
        if r.status_code != 200 and r.status_code != 201:
            checklib.quit(checklib.Status.DOWN, 'Request failure',
                          f'put_flag http://{service_addr}/api/register (username={username}, password={password}): {r.status_code}\n{r.text}')

        sessionData = r.json()
        if 'user_id' not in sessionData or not isinstance(sessionData['user_id'], int) or 'session' not in sessionData or not isinstance(sessionData['session'], str):
            checklib.quit(checklib.Status.DOWN, 'Response error',
                          f'get_flag http://{service_addr}/api/register (username={username}, password={password}): {r.status_code}\n{r.text}')

        token = 'Bearer ' + \
            base64.b64encode(
                (str(sessionData['user_id'])+':'+sessionData['session']).encode()).decode()

        time.sleep(random.randint(SLEEP_MIN_TIME_MS, SLEEP_MAX_TIME_MS) / 1000)

        # Show product
        r = requests.get(f'http://{service_addr}:{service_port}/api/products/{product_id}',
                         headers={'Authorization': token}, timeout=5)
        if r.status_code != 200:
            checklib.quit(checklib.Status.DOWN, 'Request failure',
                          f'get_flag http://{service_addr}/api/products/{product_id}: {r.status_code}\n{r.text}')

        productData = r.json()
        if 'id' not in productData or not isinstance(productData['id'], int) or 'license' not in productData or not isinstance(productData['license'], dict) or 'mod' not in productData['license'] or not isinstance(productData['license']['mod'], str) or 'poly' not in productData['license'] or not isinstance(productData['license']['poly'], list):
            checklib.quit(checklib.Status.DOWN, 'Response error',
                          f'get_flag http://{service_addr}/api/products/{product_id}: {r.status_code}\n{r.text}')

        mod = gmpy2.mpz(productData['license']['mod'])
        poly = []
        for p in productData['license']['poly']:
            poly.append(gmpy2.mpz(p))

        # Validate license
        lic = random.choice(keys)
        if not verify_licence(lic, poly, mod):
            checklib.quit(checklib.Status.DOWN, 'Response error',
                          f'License does not validate: lic={lic}, mod={mod}, poly={poly}')

        # Download product
        r = requests.post(f'http://{service_addr}:{service_port}/api/products/{product_id}/download', data={
                          'license': lic}, headers={'Authorization': token}, timeout=10)
        if r.status_code != 200:
            checklib.quit(checklib.Status.DOWN, 'Request failure',
                          f'get_flag http://{service_addr}/api/products/{product_id}/download (license={lic}): {r.status_code}\n{r.text}')

        if flag not in r.text:
            checklib.quit(checklib.Status.DOWN, 'Response error',
                          f'put_flag http://{service_addr}/api/products/{product_id}/download (license={lic}): {r.status_code}\n{r.text}')

    except (requests.ConnectTimeout, requests.ReadTimeout, requests.Timeout) as e:
        checklib.quit(checklib.Status.DOWN, 'Connection timeout', str(e))
    except requests.ConnectionError as e:
        checklib.quit(checklib.Status.DOWN, 'Connection error', str(e))
    except (json.decoder.JSONDecodeError, ValueError) as e:
        checklib.quit(checklib.Status.DOWN, 'Response error', str(e))

    checklib.quit(checklib.Status.OK, 'OK')


# VULNS:
# - In create_licences: it is wrong to start from [0,1]; this allows licences like AAAAAA-AAAAAA-AAAAAAA-AAAAAA to always pass
#   Fix: start from [1]
# - In create_licences: it is wrong to get mod as a prime number, since you can easily solve for the licences knowing the polynomial
#   Fix: mod = next_prime(random.getrandbits(1024))*next_prime(random.getrandbits(1024))
# - In create_licences: if n is small enough, since licences << mod you can find small roots with LLL and find licences (for reference: like n=5 allows to retrieve licences)
#   Fix: bigger licences/smaller modulus in order to make LLL unfeasible
# - In verify_licence: checks on the number of characters of the licences are missing, so you can craft infinite valid licences from a known one. Probably useless.
def multiply_poly(a, b, mod):
    res = [0] * (len(a) + len(b) - 1)
    for i in range(len(a)):
        for j in range(len(b)):
            res[i+j] += a[i]*b[j]
            res[i+j] %= mod
    return res


def eval_poly(coefs, x, mod):
    res = 0
    for i, c in enumerate(coefs):
        res += c*pow(x, i, mod)
        res %= mod
    return res


def num_to_list(x):
    if x < 26:
        return [x]
    return [x % 26] + num_to_list(x//26)


def licence_to_string(x):
    alph = string.ascii_uppercase
    lic = ''.join([alph[i] for i in num_to_list(x)])
    while len(lic) % 7 != 0:
        lic += "A"
    return '-'.join([lic[i:i+7] for i in range(0, len(lic), 7)])


def create_licences(n, app_secret, flag_id):
    mod = gmpy2.next_prime(random.getrandbits(1024))
    licences = [random.getrandbits(128) for _ in range(n)]
    poly = multiply_poly(
        [0, 1], [int(hashlib.sha512(app_secret + flag_id).hexdigest(), 16), 1], mod)
    for lic in licences:
        poly = multiply_poly(poly, [-lic, 1], mod)

    return (poly, mod, [licence_to_string(x) for x in licences])


def verify_licence(x, poly, mod):
    alph = string.ascii_uppercase
    real_lic = x.replace("-", "")
    real_lic = [alph.index(c) for c in real_lic]
    real_lic = sum(c*26**i for i, c in enumerate(real_lic))
    return eval_poly(poly, real_lic, mod) == 0


if __name__ == "__main__":

    if action == checklib.Action.CHECK_SLA.name:
        check_sla()
    elif action == checklib.Action.PUT_FLAG.name:
        put_flag()
    elif action == checklib.Action.GET_FLAG.name:
        get_flag()
