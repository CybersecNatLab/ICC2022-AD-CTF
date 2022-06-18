#!/usr/bin/env python3

# Do not make modification to checklib.py (except for debug), it can be replaced at any time
from string import hexdigits
import checklib
import requests
from service1_common import *
import socketio
import re
import random

data = checklib.get_data()
action = data['action']
team_id = data['teamId']
service_addr = '10.60.' + team_id + '.1'
service_name = 'ClosedSea-1'

nft_id_regex = re.compile('/view/(.*)\'><i', re.I)


# Check SLA
def check_sla():

    sess = requests.Session()
    set_rand_ua(sess)
    username, password = create_user_cred()  # User for the headless
    username_mint, password_mint = create_user_cred()  # Minter user
    global status, msg_public, msg_debug
    status, msg_public, msg_debug = checklib.Status.ERROR, 'error', 'No exit code provided'

    user_data = {
        'username': username,
        'password': password
    }

    #
    sio = socketio.Client(reconnection_attempts=3)
    try:
        sio.connect(headless_host)
    except:
        checklib.quit(checklib.Status.ERROR,
                      'Could not check.', 'Headless down')

    nft_data = randstr(10, 20)
    nft_data_donations = randstr(10, 20)
    nft_id = ''

    def check_response_ok_global(resp, status_to_check=200, in_resp=False, msg='', sio=False):
        global status, msg_public, msg_debug

        status_check = resp and status_to_check == resp.status_code
        in_resp_check = resp and in_resp and in_resp in resp.text

        if not resp or not status_check or not in_resp_check:
            msg_debug = resp.text if resp else 'Requests connection failed'
            status, msg_public, msg_debug = checklib.Status.DOWN, msg, msg_debug
            sio.disconnect()
            quit()

    # When the headless is ready, register the headless user
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
            sio.emit('register', user_data,
                     callback=lambda x: check(x))  # register
        except:
            pass

    # When the registration is done, check that the user is actually registered
    @sio.event
    def user_registered():
        global status, msg_public, msg_debug
        # Create a "minter" user, that will mint a dummy nft
        sess = requests.Session()
        set_rand_ua(sess)
        resp = register_user(sess, username_mint, password_mint,
                             randstr(128, dictionary=hexdigits))
        check_response_ok_global(
            resp, in_resp=username_mint, msg='Could not register user', sio=sio)

        # Retrieve the headless user_id
        minter_user_id = re.findall(r'user_id: \'(.*)\',', resp.text)

        try:
            minter_user_id = minter_user_id[0]
        except:
            status, msg_public, msg_debug = checklib.Status.DOWN, 'Could not retrieve user_id', resp.text
            sio.disconnect()
            quit()

        resp = login_user_minter(sess, username_mint, password_mint)
        check_response_ok_global(
            resp, in_resp='Mint an nft', msg='Could not login user on minter', sio=sio)

        # Mint a dummy NFT
        rand_title1 = randstr(1, dictionary=nft_adj) + ' ' + randstr(1,
                                                                     dictionary=nft_animals) + ' n:' + randstr(2, 8, string.digits)
        resp = mint(sess, rand_title1, nft_data,
                    random.randint(2, 6000000), 'false')
        check_response_ok_global(
            resp, in_resp='Check your new NFT!', msg='Minting not working', sio=sio)

        # Retrieve the id of the nft
        global nft_id
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

        # Visit the scoreboard
        try:
            resp = sess.get(closedsea_baseurl + '/dashboard')
        except:
            resp = False
        # Check that the nft is in the dashboard
        check_response_ok_global(
            resp, in_resp=nft_data, msg='Minting not working', sio=sio)

        # Test the donation. The headless user (username,password) will mint an NFT
        # It will then donate it to the minter user (username_mint, password_mint)
        #
        sess = requests.Session()
        set_rand_ua(sess)
        login_user_minter(sess, username, password)
        # Mint a random nft
        donation_title = randstr(1, dictionary=nft_adj) + ' ' + randstr(
            1, dictionary=nft_animals) + ' n:' + randstr(2, 8, string.digits)
        resp = mint(sess, donation_title, nft_data_donations,
                    random.randint(1000000, 10000000), 'false')
        check_response_ok_global(
            resp, in_resp='Check your new NFT!', msg='Minting not working', sio=sio)

        # Retrieve the id of the nft
        nft_id = re.findall(nft_id_regex, resp.text)
        try:
            nft_id = nft_id[0]
        except:
            status, msg_public, msg_debug = checklib.Status.DOWN, 'Could not retrieve nft_id', resp.text
            sio.disconnect()
            quit()
        sio.emit('donate', {'nft_id': nft_id, 'to': minter_user_id})

    @sio.event
    def donated():
        global status, msg_public, msg_debug
        sess = requests.Session()
        set_rand_ua(sess)
        resp = login_user_closedsea(sess, username_mint, password_mint)
        check_response_ok_global(
            resp, in_resp=username_mint, msg='Cannot login on closedsea', sio=sio)

        check_response_ok_global(
            resp, in_resp=nft_data_donations, msg='Cannot donate nft', sio=sio)

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
    if status != checklib.Status.ERROR:
        checklib.quit(status, msg_public, msg_debug)

    status, msg_public, msg_debug = checklib.Status.ERROR, '', ''

    # Check that the websocket are actually working
    sio_closedsea = socketio.Client(reconnection_attempts=3)

    @sio_closedsea.on('connect')
    def connect_closesea():
        global nft_id

        sio_closedsea.emit('transactions_for_nft', nft_id)

    @sio_closedsea.event
    def transactions_resp(result):
        global status, msg_public, msg_public
        status, msg_public, msg_debug = checklib.Status.OK, 'OK', ''
        try:
            # Check that the result is an aray and has something inside
            r = result[0]
            status, msg_public, msg_debug = checklib.Status.OK, 'OK', ''
        except:
            status, msg_public, msg_debug = checklib.Status.DOWN, 'Live transaction not working', ''

        sio_closedsea.disconnect()
        quit()

    @sio_closedsea.event
    def connect_error(data):
        print("The connection failed!")
        status, msg_public, msg_debug = checklib.Status.DOWN, 'Website is down', 'Websec connection to the website went down'
        sio_closedsea.disconnect()
        quit()

    try:
        sio_closedsea.connect(closedsea_baseurl)
    except:
        checklib.quit(checklib.Status.DOWN,
                      'Live transaction feed down', 'Websocket down')
    sio_closedsea.wait()

    checklib.quit(status, msg_public, msg_debug)


# Put the flag using the flag as the seed for random stuff
def put_flag():
    data = checklib.get_data()

    flag = data['flag']

    sess = requests.Session()
    set_rand_ua(sess)

    set_seed(flag)
    username, password = create_user_cred()

    resp = register_user(sess, username, password,
                         randstr(128, dictionary=hexdigits))
    check_response_ok(resp, in_resp=username, msg='Could not register user')

    resp = login_user_minter(sess, username, password)
    check_response_ok(resp, in_resp='Mint an nft',
                      msg='Could not login user on minter')

    flag_title = randstr(1, dictionary=nft_adj) + ' ' + randstr(1,
                                                                dictionary=nft_animals) + ' n:' + randstr(2, 8, string.digits)

    resp = mint(sess, flag_title, flag, random.randint(2, 50), 'false')
    check_response_ok(resp, in_resp='Check your new NFT!',
                      msg='Minting not working')

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
        resp, in_resp=flag, msg='Cannot insert the flag.')

    # Check that the websocket are actually working

    checklib.post_flag_id(service_name, service_addr, flag_id)
    checklib.quit(checklib.Status.OK, 'OK')


# Check if the flag still exists, use the flag as the seed for random stuff as for put flag
def get_flag():

    team_ip = '10.60.' + data['teamId'] + '.1'
    flag = data['flag']

    sess = requests.Session()
    set_rand_ua(sess)

    set_seed(flag)
    username1, password1 = create_user_cred()

    resp = login_user_closedsea(sess, username1, password1)
    check_response_ok(resp, in_resp=username1,
                      msg='Login on closedsea not working')
    try:
        resp = sess.get(closedsea_baseurl + '/dashboard')
    except:
        resp = False
    check_response_ok(resp, in_resp=flag, msg='Cannot find flag 1')

    checklib.quit(checklib.Status.OK, 'OK')


if __name__ == "__main__":

    if action == checklib.Action.CHECK_SLA.name:
        check_sla()
    elif action == checklib.Action.PUT_FLAG.name:
        put_flag()
    elif action == checklib.Action.GET_FLAG.name:
        get_flag()
