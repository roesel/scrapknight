#!flask/bin/python

from app import app
from app.config import RunConfig

app.run(**RunConfig)
