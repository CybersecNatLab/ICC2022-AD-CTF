import random
import string
import checklib
import sys

# TODO: RANDOMIZE USER AGENT
data = checklib.get_data()
action = data['action']


if len(sys.argv) > 1:
    headless_host = 'http://localhost:3000'
    team_ip = 'localhost'
else:
    headless_host = 'http://headless_team_{}:3000/'.format(data['teamId'])
    team_ip = '10.60.' + data['teamId'] + '.1'

closedsea_baseurl = 'http://{}:3003'.format(team_ip)
minter_baseurl = 'http://{}:3004'.format(team_ip)

nft_adj = [
'Candid',
'Canine',
'Capital',
'Carefree',
'Careful',
'Difficult',
'Dizzy',
'Focused',
'Fond',
'Foolhardy',
'Impressive',
'Improbable',
'Meaty',
'Medical',
'Mediocre'
]

nft_animals = [
'Albatross',
'Alligator',
'Alpaca',
'Angelfish',
'Armadillo',
'Beaver',
'Bee',
'Beetle',
'Coati',
'Cobra',
'Cockroach',
'Eagle',
'Earwig',
'Echidna',
'Gopher',
'Gorilla',
'Goshawk',
'Lemming',
'Lemur',
'Leopard',
'Squid',
'Squirrel',
'Starfish',
'Starling',
'Wolf',
'Wolverine',
'Wombat',
'Woodcock'
]

def check_response_ok(resp, status=200, in_resp=False, msg='', sio=False):

    status_check = resp and status == resp.status_code

    in_resp_check = resp and in_resp and in_resp in resp.text

    if not resp or not status_check or not in_resp_check:
        msg_debug = resp.text if resp else 'Requests connection failed'
        if sio:
            sio.disconnect()
        checklib.quit(
            checklib.Status.DOWN,
            msg,
            msg_debug
        )


def randstr(n, l=False,dictionary=string.ascii_letters):
    if l:
        n = random.randint(n, l)
    return ''.join([random.choice(dictionary) for _ in range(n)])

def set_seed(seed):
    random.seed(seed)

def register_user(sess,username, password, key):
    URL = closedsea_baseurl + '/register'

    data = {
        'username': username,
        'password': password,
        'public_key': key
    }
    try:
        return sess.post(URL, data=data)
    except:
        return False


def login_user_closedsea(sess, username, password):
    URL = closedsea_baseurl + '/login'

    data = {
        'username': username,
        'password': password
    }
    try:
        return sess.post(URL, data=data)
    except:
        return False


def login_user_minter(sess, username, password):
    URL = minter_baseurl + '/login.php'
    data = {
        'username': username,
        'password': password
    }
    try:
        return sess.post(URL, data=data)
    except:
        return False


def mint(sess, title, data, cost, is_public):
    URL = minter_baseurl + '/index.php'
    data ={
        'title': title,
        'data': data,
        'price': cost,
        'public': is_public
    }
    try:
        return sess.post(URL, data=data)
    except:
        return False

def logout(sess):
    URL = closedsea_baseurl + '/logout'
    try:
        return sess.get(URL)
    except:
        return False

def list_all_nfts(sess):
    URL = closedsea_baseurl + '/listing'
    pass

def list_all_nfts_websockets(sess):
    pass

def create_user_cred():
    username =  randstr(6,9)
    password = randstr(6,9)
    return username, password

def set_rand_ua(sess):
    with open('user_agents.txt', 'r') as f:
        ua_list = f.readlines()

    sess.headers.update({'User-Agent': random.choice(ua_list)[:-1]})
