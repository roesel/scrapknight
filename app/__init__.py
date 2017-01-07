import os
import json
import datetime

from flask import Flask, url_for, redirect, \
    render_template, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError

from .forms import InputForm

from tools import process, users_cards_save, print_user_library, print_user_deck
from libs.builder import Builder

"""App Configuration"""

from .config import FlaskConfig
from .config import GoogleAuthConfig
from .config import DatabaseConfig

"""APP creation and configuration"""
app = Flask(__name__)
app.config.from_object(FlaskConfig)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"

from libs.database import Database
from tools import Deck

""" DB Models """

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(200))
    tokens = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    def save_cards(self, deck):

        for card in deck.cards:
            if card.found:
                query = """
                    INSERT INTO `users_cards`
                    (`user_id`, `card_id`, `count`)
                    VALUES
                    (%s, %s, 1)
                    ON DUPLICATE KEY UPDATE count=count+1
                    """

                self.db.insert(
                    query, (self.id, card.id,))

    def get_library(self):

        query = """
            SELECT `card_id`, `count`
            FROM `users_cards`
            WHERE `user_id` = %s
            """

        cards = self.db.query(query, (self.id,))
        library = [{'id': c[0], 'count': c[1]} for c in cards]

        return Deck(card_list=library)

    def get_deck(self, deck_id):

        query = """
            SELECT `c`.`card_id`, `c`.`count`
            FROM `users_decks` AS `d`
            INNER JOIN `users_decks_cards` AS `c`
            ON `d`.`id` = `c`.`deck_id`
            WHERE `d`.`user_id` = %s AND `d`.`id` = %s
            """

        cards = self.db.query(query, (self.id, deck_id,))
        deck = [{'id': c[0], 'count': c[1]} for c in cards]

        return Deck(card_list=deck)

User.db = Database(DatabaseConfig)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
""" OAuth Session creation """


def get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(GoogleAuthConfig.CLIENT_ID, token=token)
    if state:
        return OAuth2Session(
            GoogleAuthConfig.CLIENT_ID,
            state=state,
            redirect_uri=GoogleAuthConfig.REDIRECT_URI)
    oauth = OAuth2Session(
        GoogleAuthConfig.CLIENT_ID,
        redirect_uri=GoogleAuthConfig.REDIRECT_URI,
        scope=GoogleAuthConfig.SCOPE)
    return oauth


@app.route('/')
def index():
    # return render_template('appindex.html')
    form = InputForm()
    return render_template(
        'input.html',
        title='Input',
        fill='',
        form=form)


@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    google = get_google_auth()
    auth_url, state = google.authorization_url(
        GoogleAuthConfig.AUTH_URI, access_type='offline')
    session['oauth_state'] = state

    # Since we login only with google, we can skip the "login" page.
    # return render_template('login.html', auth_url=auth_url)
    return redirect(auth_url)


@app.route('/gCallback')
def callback():
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('index'))
    if 'error' in request.args:
        if request.args.get('error') == 'access_denied':
            return 'You denied access.'
        return 'Error encountered.'
    if 'code' not in request.args and 'state' not in request.args:
        return redirect(url_for('login'))
    else:
        google = get_google_auth(state=session['oauth_state'])
        try:
            token = google.fetch_token(
                GoogleAuthConfig.TOKEN_URI,
                client_secret=GoogleAuthConfig.CLIENT_SECRET,
                authorization_response=request.url)
        except HTTPError:
            return 'HTTPError occurred.'
        google = get_google_auth(token=token)
        resp = google.get(GoogleAuthConfig.USER_INFO)
        if resp.status_code == 200:
            user_data = resp.json()
            email = user_data['email']
            user = User.query.filter_by(email=email).first()
            if user is None:
                user = User()
                user.email = email
            user.name = user_data['name']
            print(token)
            user.tokens = json.dumps(token)
            user.avatar = user_data['picture']
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
        return 'Could not fetch your information.'


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/savecards', methods=['POST'])
@login_required
def savecards():

    card_list = request.form['card_list']

    users_cards_save(current_user, card_list)

    return "success"

@app.route('/library')
@login_required
def library():

    bu = Builder(DatabaseConfig)

    headers, results, footer, success, log = print_user_library(current_user)

    return render_template(
        'library.html',
        title='Library',
        form="",
        results_header=headers,
        results=results,
        results_footer=footer,
        results_success=success,
        fill="",
        log=log,
        db_info=bu.get_db_info())

@app.route('/deck/<int:deck_id>')
@login_required
def deck(deck_id):

    bu = Builder(DatabaseConfig)

    deck_table, log_1 = print_user_deck(current_user, deck_id)
    library_table, log_2 = print_user_library(current_user)

    log = [log_1, log_2]

    return render_template(
        'deck.html',
        title='Deck',
        form="",
        deck_table=deck_table,
        library_table=library_table,
        fill="",
        log=log,
        db_info=bu.get_db_info())

@app.route('/input', methods=['GET', 'POST'])
def input():

    form = InputForm()
    bu = Builder(DatabaseConfig)
    if form.validate_on_submit():
        #flash( 'Input containted: %s' % (form.text.data) )
        # return redirect('/')

        output_table, log = process(form.text.data)

        return render_template(
            'input.html',
            title='Output',
            form=form,
            output_table=output_table,
            fill=form.text.data,
            log=log,
            db_info=bu.get_db_info())

    return render_template(
        'input.html',
        title='Input',
        fill='',
        form=form)
