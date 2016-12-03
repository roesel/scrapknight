from flask import render_template, flash, redirect
from app import app
from .forms import InputForm
from tools import *

@app.route('/')

@app.route('/index')
def index():
    user = {'nickname': 'Miguel'}  # fake user
    return render_template('index.html',
                           title='Home',
                           user=user)

@app.route('/input', methods=['GET', 'POST'])
def input():
    form = InputForm()
    if form.validate_on_submit():
        #flash( 'Input containted: %s' % (form.text.data) )
        #return redirect('/')

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
            log=log)

    return render_template(
        'input.html',
        title='Input',
        fill='',
        form=form)
