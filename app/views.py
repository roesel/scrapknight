from flask import render_template, flash, redirect, request, json
from app import app
from .forms import InputForm

from config_db import config
from tools import process, users_cards_save
from libs.builder import Builder

from oauth2client import client, crypt

def valitade_google_token(token):
    try:
        idinfo = client.verify_id_token(token, '442163098457-s25477neik7u550umg0fv2kkn5h9n4rm.apps.googleusercontent.com')

        # Or, if multiple clients access the backend server:
        #idinfo = client.verify_id_token(token, None)
        #if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
        #    raise crypt.AppIdentityError("Unrecognized client.")

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise crypt.AppIdentityError("Wrong issuer.")

        # If auth request is from a G Suite domain:
        #if idinfo['hd'] != GSUITE_DOMAIN_NAME:
        #    raise crypt.AppIdentityError("Wrong hosted domain.")
    except crypt.AppIdentityError:
        raise crypt.AppIdentityError("Invalid token.")

    return idinfo

@app.route('/')
@app.route('/index')
def index():
    user = {'nickname': 'Miguel'}  # fake user
    return render_template('index.html',
                           title='Home',
                           user=user)


@app.route('/tokensignin', methods=['POST'])
def tokensignin():
    # (Receive token by HTTPS POST)
    token = request.form['id_token']
    idinfo = valitade_google_token(token)

    return flask.jsonify(**idinfo)

@app.route('/savecards', methods=['POST'])
def savecards():
    # (Receive token by HTTPS POST)
    token = request.form['id_token']
    idinfo = valitade_google_token(token)
    userid = idinfo['sub']

    card_list = request.form['card_list']
    bu = Builder(config)

    print(card_list)

    users_cards_save(userid, card_list)

@app.route('/input', methods=['GET', 'POST'])
def input():
    form = InputForm()
    bu = Builder(config)
    if form.validate_on_submit():
        #flash( 'Input containted: %s' % (form.text.data) )
        # return redirect('/')

        headers, results, footer, success, log = process(form.text.data)

        return render_template(
            'input.html',
            title='Output',
            form=form,
            results_header=headers,
            results=results,
            results_footer=footer,
            results_success=success,
            fill=form.text.data,
            log=log,
            db_info=bu.get_db_info())

    return render_template(
        'input.html',
        title='Input',
        fill='',
        form=form)
