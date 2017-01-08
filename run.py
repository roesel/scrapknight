#!flask/bin/python

from app import app
from app.config import RunConfig

from pprint import pprint

app.jinja_env.line_comment_prefix = '##'
app.jinja_env.line_statement_prefix = '#'

# pprint(vars(app.jinja_env))

app.run(**RunConfig)
