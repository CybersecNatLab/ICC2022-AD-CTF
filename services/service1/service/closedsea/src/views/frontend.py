from flask import Blueprint, current_app, redirect, render_template, url_for, request, flash, session
from flask import abort, g
from .exceptions import WrongPassword
import sys
from .helpers import do_query, is_logged, logged, login_user, not_logged, register_user, get_public_nft, user_has_nft
from .helpers import retrieve_user, retrieve_nft, retrieve_user_nfts, retrieve_user_public_nfts, is_nft_public
import requests


frontend = Blueprint('frontend', 'frontend')


@frontend.before_request
def add_g():
    if is_logged():
        g.user = retrieve_user(session['id'])


@frontend.get('/')
def index():
    minter_url = request.host_url.replace("3003", "3004")
    return render_template('index.html', minter_url=minter_url)


@frontend.get('/login')
@not_logged
def login_page():
    minter_url = request.host_url.replace("3003", "3004")
    return render_template('login.html', minter_url=minter_url)


@frontend.post('/login')
@not_logged
def login():
    username = request.form.get('username', False)
    password = request.form.get('password', False)

    if not all((username, password)):
        flash('You need to provide an username, a password')
        return redirect(url_for('frontend.register'))

    try:
        user_id, public_key = login_user(username, password)
    except WrongPassword:
        flash('Wrong username or password')
        return redirect(url_for('frontend.login'))

    session['username'] = username
    session['id'] = user_id
    session['public_key'] = public_key

    flash('Success')
    return redirect(url_for('frontend.dashboard'))


@frontend.get('/register')
@not_logged
def register_page():
    minter_url = request.host_url.replace("3003", "3004")
    return render_template('register.html', minter_url=minter_url)


@frontend.post('/register')
@not_logged
def register():
    username = request.form.get('username', False)
    password = request.form.get('password', False)
    public_key = request.form.get('public_key', False)

    if not all((username, password, public_key)):
        flash('You need to provide an username, a password and a public_key')
        return redirect(url_for('frontend.register'))
    username = username.replace("'", "")
    if not (user_id := register_user(username, password, public_key)):
        flash('Error')
        return redirect(url_for('frontend.register'))

    # Everything seems good!
    session['username'] = username
    session['id'] = user_id
    session['public_key'] = public_key

    flash('Success')
    return redirect(url_for('frontend.dashboard'))


@frontend.get('/logout')
@logged
def logout():
    del session['username']
    del session['id']
    del session['public_key']
    return redirect(url_for('frontend.index'))


@frontend.get('/dashboard')
@logged
def dashboard():
    nfts = retrieve_user_nfts(session['id'])
    minter_url = request.host_url.replace("3003", "3004")
    return render_template('dashboard.html', nfts=nfts, minter_url=minter_url)


@frontend.get('/listing')
def listing():

    minter_url = request.host_url.replace("3003", "3004")
    page = request.args.get('p', 0)
    try:
        page = int(page)
    except ValueError:
        page = 0

    if page < 0:
        abort(404)
    offset = page*10
    n = 10

    nfts = get_public_nft(offset, n)
    return render_template('listing.html', nfts=nfts, page=page, minter_url=minter_url)


@frontend.get('/view/<nft_id>')
def view(nft_id):
    minter_url = request.host_url.replace("3003", "3004")
    nft = retrieve_nft(nft_id)
    if not nft:
        abort(404)
    own = False
    if session.get('id', False):
        own = user_has_nft(session['id'], nft_id)
    return render_template('item.html', nft=nft, own=own, minter_url=minter_url)


@frontend.get('/user/<user_id>')
def user(user_id):
    minter_url = request.host_url.replace("3003", "3004")
    user = retrieve_user(user_id)
    if not user:
        abort(404)

    nfts = retrieve_user_public_nfts(user_id)

    return render_template('user.html', user=user, nfts=nfts, minter_url=minter_url)


@frontend.post('/switch/<nft_id>')
@logged
def switch(nft_id):
    API_BUY = current_app.config['TRANSACTION_BASE'] + '/switch_chain'
    nft = retrieve_nft(nft_id)
    if not nft:
        abort(404)

    user_id = str(session['id'])
    if not user_has_nft(user_id, nft_id):
        flash('You don\'t own this NFT!')
        return redirect(url_for('frontend.view', nft_id=nft_id))

    chain = request.form.get('chain', 0)
    data = {
        'nft_id': nft_id,
        'user_id': user_id,
        'chain': chain
    }
    result = requests.post(API_BUY, json=data).json()
    if result['success']:
        return redirect(url_for('frontend.view', nft_id=nft_id))
    flash(result['message'])
    return redirect(url_for('frontend.view', nft_id=nft_id))


@frontend.post('/buy/<nft_id>')
@logged
def buy(nft_id):
    API_BUY = current_app.config['TRANSACTION_BASE'] + '/buy'
    nft = retrieve_nft(nft_id)
    if not nft:
        abort(404)

    user_id = str(session['id'])
    if user_has_nft(user_id, nft_id):
        flash('You already have this nft')
        return redirect(url_for('frontend.view', nft_id=nft_id))

    if not is_nft_public(nft_id):
        flash('This NFT is private! You cannot buy it!')
        return redirect(url_for('frontend.view', nft_id=nft_id))

    signature = request.form.get('signature', False)
    if not signature:
        flash('You need to sign the transaction')
        return redirect(url_for('frontend.view', nft_id=nft_id))

    data = {
        'nft_id': nft_id,
        'user_id': user_id,
        'signature': signature,
        'pubkey': session['public_key']
    }
    result = requests.post(API_BUY, json=data).json()
    if result['success']:
        return redirect(url_for('frontend.view', nft_id=result["new_id"]))

    flash(result['message'])
    return redirect(url_for('frontend.view', nft_id=nft_id))


@frontend.post('/donate/<nft_id>')
@logged
def donate(nft_id):
    API_DONATE = current_app.config['TRANSACTION_BASE'] + '/donate'
    nft = retrieve_nft(nft_id)

    if not nft:
        abort(404)

    signature = request.form.get('signature', False)
    if not signature:
        flash('You need to sign the transaction')
        return redirect(url_for('frontend.view', nft_id=nft_id))

    # Actual donate
    to_addr = request.form.get('to_addr', False)

    to_user = retrieve_user(to_addr)
    if not to_user:
        flash('Cannot find recipient')
        return redirect(url_for('frontend.view', nft_id=nft_id))

    data = {
        'nft_id': nft_id,
        'from_addr': nft["owner"],
        'to_addr': to_addr,
        'signature': signature,
        'pubkey': session['public_key']
    }
    result = requests.post(API_DONATE, json=data).json()

    if 'success' in result and result['success']:
        flash("Succesfully donated!")
        return redirect(url_for('frontend.view', nft_id=result['new_id']))
    try:
        flash(result['message'])
    except:
        flash('Something went wrong')
    return redirect(url_for('frontend.view', nft_id=nft_id))
