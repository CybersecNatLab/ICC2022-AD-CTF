from .exceptions import NotLogged, WrongPassword
from flask import request, session, flash, redirect, url_for, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import uuid

def logged(func):
    @wraps(func)
    def f(*args, **argv):
        if not is_logged():
            flash('You need to sign-in first to do that')
            return redirect(url_for('frontend.login_page'))
        return func(*args, **argv)
    return f

def not_logged(func):
    @wraps(func)
    def f(*args, **argv):
        if is_logged():
            return redirect(url_for('frontend.index'))
        return func(*args, **argv)
    return f

def get_current_user():
    if not is_logged():
        raise NotLogged()

    return session['username']

def is_logged():
    return 'username' in session

def do_query(query, params, commit=False):
    cursor = g.mysql.connection.cursor()
    cursor.execute(query, params)

    if commit:
        g.mysql.connection.commit()
    result = cursor.fetchall()
    insertObject = []
    try:
        columnNames = [column[0] for column in cursor.description]

        for record in result:
            insertObject.append( dict( zip( columnNames , record ) ) )
    except TypeError:
        return None
    finally:
        cursor.close()
    return insertObject

def register_user(username, password, public_key):

    user_id = uuid.uuid4()
    query = 'INSERT INTO users (id, username,password, public_key) VALUES (%s, %s, %s, %s)'

    password_hash = generate_password_hash(password)
    try:
        do_query(query, [user_id, username, password_hash, public_key], commit=True)
    except:
        return False
    return user_id


def login_user(username, password):
    query = 'SELECT id, public_key, password FROM users WHERE username = %s'
    result = do_query(query, [username])

    if len(result) != 1:
        raise WrongPassword
    password_hash = result[0]['password']

    if not check_password_hash(password_hash, password):
        raise WrongPassword

    return result[0]['id'], result[0]['public_key']

def get_public_nft(offset, number):
    query = 'SELECT * FROM nfts JOIN nft_chain ON nfts.nft_id = nft_chain.nft_id WHERE price != 0 and nft_chain.chain_number=TRUE ORDER BY nft_created DESC LIMIT %s,%s'
    result = do_query(query, [offset, number])

    return result

def retrieve_user(user_id):
    query = 'SELECT * FROM users WHERE id = %s'
    user = do_query(query, [user_id])
    if len(user) < 1:
        return False
    return user[0]

def retrieve_nft(nft_id):
    query = 'SELECT * FROM nfts JOIN nft_chain on nfts.nft_id = nft_chain.nft_id WHERE nfts.nft_id = %s'
    nft = do_query(query, [nft_id])
    if len(nft) < 1:
        return False
    return nft[0]

def is_nft_public(nft_id):
    query = 'SELECT * FROM nfts JOIN nft_chain on nfts.nft_id = nft_chain.nft_id WHERE nfts.nft_id = %s and nft_chain.chain_number = 1'
    nft = do_query(query, [nft_id])
    return len(nft) == 1
        
def user_has_nft(user, nft_id):
    query = 'SELECT * FROM nfts WHERE nft_id = %s and owner = %s'
    nft = do_query(query, [nft_id, user])
    return len(nft) > 0

def retrieve_user_nfts(user):
    query = 'SELECT * FROM nfts JOIN nft_chain on nfts.nft_id = nft_chain.nft_id WHERE nfts.owner = %s'
    nft = do_query(query, [user])

    return nft

def retrieve_user_public_nfts(user):
    query = 'SELECT * FROM nfts JOIN nft_chain on nfts.nft_id = nft_chain.nft_id WHERE nfts.owner = %s and nft_chain.chain_number=TRUE'
    nft = do_query(query, [user])

    return nft
