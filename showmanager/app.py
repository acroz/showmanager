
import os
import flask
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from flask_sqlalchemy import SQLAlchemy
#from flask.ext.login import LoginManager

# Create the flask app
app = flask.Flask(__name__)

# Add bootstrap templates
Bootstrap(app)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

# Create navbar
nav = Nav()
@nav.navigation()
def topbar():
    bar = Navbar('LeagueManager',
                 View('Leagues', 'leagues'))
    return bar
nav.init_app(app)

# Add the database
dirname = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dbfile = os.path.join(dirname, 'test.db')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + dbfile
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
