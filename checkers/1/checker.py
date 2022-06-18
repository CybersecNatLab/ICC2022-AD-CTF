#!/usr/bin/env python3

# Do not make modification to checklib.py (except for debug), it can be replaced at any time
from string import hexdigits
import checklib
import requests
from service1_common import *
import socketio
from time import sleep
import re

data = checklib.get_data()
action = data['action']
team_id = data['teamId']
service_addr = '10.60.' + team_id + '.1'
service_name = 'ClosedSea-2'


# Check SLA
def check_sla():

    sess = requests.Session()
    set_rand_ua(sess)
    username, password = create_user_cred()
    username_mint, password_mint = create_user_cred()
    user_data = {
        'username': username,
        'password': password
    }

    # Because socketio spawns another thread, we have to save the exit informations here. I feel dirty for this code
    global status, msg_public, msg_debug
    status, msg_public, msg_debug = checklib.Status.ERROR, 'error', 'No exit code provided'
    sio = socketio.Client(reconnection_attempts=3)
    try:
        sio.connect(headless_host)
    except:
        checklib.quit(checklib.Status.ERROR,
                      'Could not check.', 'Headless down')

    nft_data = randstr(10, 20)

    def check_response_ok_global(resp, status_to_check=200, in_resp=False, msg='', sio=False):
        global status, msg_public, msg_debug

        status_check = resp and status_to_check == resp.status_code
        in_resp_check = resp and in_resp and in_resp in resp.text

        if not status_check or not in_resp_check:
            msg_debug = resp.text if resp else 'Requests connection failed'
            status, msg_public, msg_debug = checklib.Status.DOWN, msg, msg_debug
            sio.disconnect()
            quit()

    @sio.event
    def ready():
        def check(msg):
            global status, msg_public, msg_debug
            if not msg or msg['error']:
                status, msg_public, msg_debug = checklib.Status.DOWN, 'Website down', 'headless:' + \
                    str(msg)
                sio.disconnect()
                quit()
            return True
        try:
            sio.emit('register', user_data, callback=lambda x: check(x))
        except:
            pass

    @sio.event
    def user_registered():
        global status, msg_public, msg_debug
        # Create a "minter" user, that will mint a dummy nft
        resp = register_user(sess, username_mint, password_mint,
                             randstr(128, dictionary=hexdigits))
        check_response_ok_global(
            resp, in_resp=username_mint, msg='Could not register user', sio=sio)
        resp = login_user_minter(sess, username_mint, password_mint)
        check_response_ok_global(
            resp, in_resp='Mint an nft', msg='Could not login user on minter', sio=sio)

        # Mint a dummy NFT
        rand_title1 = randstr(1, dictionary=nft_adj) + ' ' + randstr(1,
                                                                     dictionary=nft_animals) + ' n:' + randstr(2, 8, string.digits)

        resp = mint(sess, rand_title1, nft_data, random.randint(2, 6), 'true')
        check_response_ok_global(
            resp, in_resp='Check your new NFT!', msg='Minting not working', sio=sio)

        # Retrieve the id of the nft
        nft_id_regex = re.compile('/view/(.*)\'><i', re.I)
        nft_id = re.findall(nft_id_regex, resp.text)
        try:
            nft_id = nft_id[0]
        except:
            status, msg_public, msg_debug = checklib.Status.DOWN, 'Could not retrieve nft_id', resp.text
            sio.disconnect()
            quit()

        # Visit the view page
        try:
            resp = sess.get(closedsea_baseurl + '/view/' + nft_id)
        except:
            resp = False
        check_response_ok_global(
            resp, in_resp=nft_data, msg='View nft not working', sio=sio)
        check_response_ok_global(
            resp, in_resp='own', msg='View nft not working', sio=sio)

        try:
            resp = sess.get(closedsea_baseurl + '/dashboard')
        except:
            resp = False
        # Check that the dummy nft is in the dashboard
        check_response_ok_global(
            resp, in_resp=nft_data, msg='Minting not working', sio=sio)

        sio.emit('buy', {'nft_id': nft_id})

    @sio.event
    def buyed():
        global status, msg_public, msg_debug
        sess = requests.Session()
        set_rand_ua(sess)
        login_user_closedsea(sess, username, password)
        try:
            resp = sess.get(closedsea_baseurl + '/dashboard')
        except:
            resp = False
        check_response_ok_global(
            resp, in_resp=nft_data, msg="Cannot buy nft", sio=sio)

        status, msg_public, msg_debug = checklib.Status.OK, 'OK', ''
        sio.disconnect()
        quit()

    @sio.event
    def connect_error(data):
        global status, msg_public, msg_debug
        status, msg_public, msg_debug = checklib.Status.ERROR, 'error', 'error: headless disconnected unexpectedly'
        sio.disconnect()
        quit()

    # wait for the headleass to finish
    sio.wait()
    checklib.quit(status, msg_public, msg_debug)


# Put the flag.
# 1) Create an account for the owner of the flag (headless)
# 2) Create an account for a "seller account" (python)
# 3) Mint a dummy nft with the seller
# 4) The headless makes a transaction and buys the dummy nft, in order to create a transanction with it's own private key
# 5) If everything above goes ok, mint the flag
def put_flag():
    data = checklib.get_data()
    set_seed(data['flag'])
    username, password = create_user_cred()
    user_data = {
        'username': username,
        'password': password
    }

    global status, msg_public, msg_debug
    status, msg_public, msg_debug = -1, 'error', 'No exit code provided'
    sio = socketio.Client(reconnection_attempts=3)
    try:
        sio.connect(headless_host)
    except:
        checklib.quit(checklib.Status.ERROR,
                      'Could not check.', 'Headless down')

    nft_data = randstr(10, 20)

    def check_response_ok_global(resp, status_to_check=200, in_resp=False, msg='', sio=False):
        global status, msg_public, msg_debug

        status_check = resp and status_to_check == resp.status_code
        in_resp_check = resp and in_resp and in_resp in resp.text

        if not status_check or not in_resp_check:
            msg_debug = resp.text if resp else 'Requests connection failed'
            status, msg_public, msg_debug = checklib.Status.DOWN, msg, msg_debug
            sio.disconnect()
            quit()

    @sio.event
    def ready():
        def check(msg):
            global status, msg_public, msg_debug
            if not msg or msg['error']:
                status, msg_public, msg_debug = checklib.Status.DOWN, 'Website down', 'headless:' + \
                    str(msg)
                sio.disconnect()
                quit()

            return True

        try:
            sio.emit('register', user_data, callback=lambda x: check(x))
        except:
            pass

    @sio.event
    def user_registered():
        global status, msg_public, msg_debug
        # Create a "minter" user, that will mint a dummy nft
        sess = requests.Session()
        set_rand_ua(sess)
        username_mint, password_mint = create_user_cred()
        resp = register_user(sess, username_mint, password_mint,
                             randstr(128, dictionary=hexdigits))
        check_response_ok_global(
            resp, in_resp=username_mint, msg='Could not register user', sio=sio)
        resp = login_user_minter(sess, username_mint, password_mint)
        resp = check_response_ok_global(
            resp, in_resp='Mint an nft', msg='Could not login user on minter', sio=sio)

        # Mint a dummy NFT
        rand_title1 = randstr(1, dictionary=nft_adj) + ' ' \
            + randstr(1, dictionary=nft_animals) + \
            ' n:' + randstr(2, 8, string.digits)

        resp = mint(sess, rand_title1, nft_data, random.randint(2, 6), 'true')
        check_response_ok_global(
            resp, in_resp='Check your new NFT!', msg='Minting not working', sio=sio)

        # Retrieve the id of the nft
        nft_id_regex = re.compile('/view/(.*)\'><i', re.I)
        nft_id = re.findall(nft_id_regex, resp.text)
        try:
            nft_id = nft_id[0]
        except:
            status, msg_public, msg_debug = checklib.Status.DOWN, 'Could not retrieve nft_id', resp.text
            sio.disconnect()
            quit()
            #checklib.quit(checklib.Status.DOWN, 'Could not retrieve nft_id', resp.text)

        login_user_closedsea(sess, username_mint, password_mint)
        try:
            resp = sess.get(closedsea_baseurl + '/dashboard')
        except:
            resp = False
        # Check that the flag is in the dashboard
        check_response_ok_global(
            resp, in_resp=nft_data, msg='Minting not working', sio=sio)

        sio.emit('buy', {'nft_id': nft_id})

    @sio.event
    def buyed():
        global status, msg_public, msg_debug
        sess = requests.Session()
        set_rand_ua(sess)
        login_user_closedsea(sess, username, password)
        try:
            resp = sess.get(closedsea_baseurl + '/dashboard')
        except:
            resp = False
        check_response_ok_global(
            resp, in_resp=nft_data, msg="Cannot buy nft", sio=sio)
        # Close the connection
        sio.disconnect()
        quit()
        #checklib.quit(checklib.Status.OK, 'OK')

    @sio.event
    def connect_error(data):
        global status, msg_public, msg_debug
        status, msg_public, msg_debug = checklib.Status.ERROR, 'error', 'error: headless disconnected unexpectedly'
        sio.disconnect()
        quit()
        #checklib.quit(checklib.Status.ERROR, 'error', 'error: headless disconnected unexpectedly')

    # wait for the headleass to finish
    sio.wait()
    if status != -1:  # If there are errors quit
        checklib.quit(status, msg_public, msg_debug)

    # Now we have made a transaction with the flag owner. Let's mint a flag
    sess = requests.Session()
    set_rand_ua(sess)

    resp = login_user_minter(sess, username, password)
    flag_title = randstr(1, dictionary=nft_adj) + ' ' + randstr(1,
                                                                dictionary=nft_animals) + ' n:' + randstr(2, 8, string.digits)
    resp = mint(sess, flag_title, data['flag'],
                random.randint(1000000, 10000000), 'true')
    check_response_ok(resp, in_resp='Check your new NFT!',
                      msg='Minting not working')
    nft_id_regex = re.compile('/view/(.*)\'><i', re.I)
    flag_id = re.findall(nft_id_regex, resp.text)
    try:
        flag_id = flag_id[0]
    except:
        checklib.quit(checklib.Status.DOWN, 'Could not mint nft', resp.text)

    login_user_closedsea(sess, username, password)
    try:
        resp = sess.get(closedsea_baseurl + '/dashboard')
    except:
        resp = False
    check_response_ok(
        resp, in_resp=data['flag'], msg='Cannot insert the flag.')
    checklib.post_flag_id(service_name, service_addr, flag_id)
    checklib.quit(checklib.Status.OK, 'OK')

# Check if the flag still exists, use the flag as the seed for random stuff as for put flag


def get_flag():

    team_ip = '10.60.' + data['teamId'] + '.1'
    flag = data['flag']

    sess = requests.Session()
    set_rand_ua(sess)

    set_seed(data['flag'])
    username1, password1 = create_user_cred()

    resp = login_user_closedsea(sess, username1, password1)
    check_response_ok(resp, in_resp=username1,
                      msg='Login on closedsea not working')
    try:
        resp = sess.get(closedsea_baseurl + '/dashboard')
    except:
        resp = False
    check_response_ok(resp, in_resp=data['flag'], msg='Cannot find flag')
    # If OK
    checklib.quit(checklib.Status.OK, 'OK')
    # If something is wrong


if __name__ == "__main__":

    if action == checklib.Action.CHECK_SLA.name:
        check_sla()
    elif action == checklib.Action.PUT_FLAG.name:
        put_flag()
    elif action == checklib.Action.GET_FLAG.name:
        get_flag()
