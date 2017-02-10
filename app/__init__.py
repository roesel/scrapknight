import os
import json
import datetime

from flask import Flask, url_for, redirect, \
    render_template, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError

from htmlmin.minify import html_minify

from .forms import InputForm

from .tools import process, users_cards_save, print_user_library, print_user_deck, \
    modify_user_deck, save_user_library, process_by_id
from libs.builder import Builder

import app.shared_stuff

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

shared_stuff.db = db

from .user import User


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
    form = InputForm()
    return html_minify(render_template(
        'home.html',
        title='Input',
        fill='',
        form=form))


@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    google = get_google_auth()
    auth_url, state = google.authorization_url(
        GoogleAuthConfig.AUTH_URI, access_type='offline')
    session['oauth_state'] = state

    # Since we login only with google, we can skip the "login" page.
    # return html_minify(render_template('login.html', auth_url=auth_url))
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


@app.route('/searchcard', methods=['POST'])
def searchcard():
    search_string = request.form['search_string']

    output_table, log = process(current_user, search_string)

    # tady html_minify() dělá nějaké problémy ... :/
    return render_template(
        'page_parts/card_search_table.html',
        search_table=output_table)


@app.route('/savecards', methods=['POST'])
@login_required
def savecards():

    card_list = request.form['card_list']

    users_cards_save(current_user, card_list)

    return "success"


@app.route('/savelibrary', methods=['POST'])
@login_required
def savelibrary():

    card_list = request.form['card_list']

    status = save_user_library(current_user, card_list)
    if status:
        return "success"
    else:
        return "failure"


@app.route('/modifydeck', methods=['POST'])
@login_required
def modifydeck():

    card_list = request.form['card_list']
    deck_id = request.form['deck_id']

    status = modify_user_deck(current_user, deck_id, card_list)
    if status:
        return "success"
    else:
        return "failure"


@app.route('/library')
@login_required
def library():

    bu = Builder(DatabaseConfig)

    decks = current_user.get_deck_list()

    for deck in decks:
        if not deck['name']:
            deck['name'] = "Deck {}".format(deck['id'])
        if not deck['card_count']:
            deck['card_count'] = 0

    if decks:
        new_id = decks[-1]['id'] + 1
    else:
        new_id = 1
    newdeck = [{
        'id': new_id,
        'name': 'New Deck',
        'card_count': '',
        'info': ''}]

    library_table, log = print_user_library(current_user)

    return html_minify(render_template(
        'library.html',
        title='Library',
        form="",
        table_of_decks_data=decks + newdeck,
        library_table=library_table,
        fill="",
        log=log,
        db_info=bu.get_db_info()))


@app.route('/deck/<int:deck_id>', methods=['GET', 'POST'])
@login_required
def deck(deck_id, search_table=None):

    form = InputForm()
    if form.validate_on_submit():
        search_table, log_0 = process(current_user, form.text.data)
    else:
        log_0 = []
        search_table = None

    bu = Builder(DatabaseConfig)

    deck_table, log_1 = print_user_deck(current_user, deck_id)
    library_table, log_2 = print_user_library(current_user)

    log = log_0 + log_1 + log_2

    return html_minify(render_template(
        'deck.html',
        title='Deck',
        form="",
        deck_table=deck_table,
        library_table=library_table,
        search_table=search_table,
        fill="",
        log=log,
        db_info=bu.get_db_info()))


@app.route('/card/<card_id>')
@login_required
def card(card_id):

    bu = Builder(DatabaseConfig)

    card_details, output_table, log = process_by_id(card_id)

    return html_minify(render_template(
        'card.html',
        title='Deck',
        form="",
        output_table=output_table,
        card_details_data=card_details,
        fill="",
        log=log,
        db_info=bu.get_db_info()))


@app.route('/input', methods=['GET', 'POST'])
def input():

    form = InputForm()
    bu = Builder(DatabaseConfig)
    if form.validate_on_submit():
        #flash( 'Input containted: %s' % (form.text.data) )
        # return redirect('/')

        output_table, log = process(current_user, form.text.data)

        return html_minify(render_template(
            'table.html',
            title='Output',
            form=form,
            output_table=output_table,
            fill=form.text.data,
            log=log,
            db_info=bu.get_db_info()))

    return html_minify(render_template(
        'home.html',
        title='Input',
        fill='',
        form=form))
