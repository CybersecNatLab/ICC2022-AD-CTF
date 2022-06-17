from flask import Flask, g
from views.frontend import frontend
from views.api import api
from flask_mysqldb import MySQL
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET', os.urandom(16))
app.config['TRANSACTION_BASE'] = os.environ.get('TRANSACTION_ENDPOINT', 'http://transactions:8085')
app.config['MYSQL_HOST'] = os.environ.get('DBHOST', 'blockchain')
app.config['MYSQL_USER'] = os.environ.get('DBUSER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('DBPASS', '')
app.config['MYSQL_DB'] = os.environ.get('DBSCHEMA', 'blockchain')


mysql = MySQL(app)

@app.before_request
def add_mysql():
    g.mysql = mysql.connection.cursor()

app.register_blueprint(frontend)
app.register_blueprint(api)
