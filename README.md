# ScrapKnight
Magic scrapper/multitool.

## Installation of dev environment

### Prerequisities
You need at least the following

* Python 3.5+
* pip

or just simply a working Anaconda installation.

### Clone this repo
Add this repository to your favourite git client. Let's assume you put it into `C:\Repa\scrapknight`.

### Setting up a virtual environment on Windows

1. Open up terminal
2. Navigate to the root of the repository
3. run `python -m venv flask`
 * (a dedicated python installation has been copied over to the folder `flask` in the repository root)
4. While still in the root of the repo, run the following commands. (Most of them are likely not necessary, but they're adopted from a tutorial, it works and it's a virtualenv anyway.)


    flask\Scripts\pip install flask
    flask\Scripts\pip install flask-login
    flask\Scripts\pip install flask-openid
    flask\Scripts\pip install flask-mail
    flask\Scripts\pip install flask-sqlalchemy
    flask\Scripts\pip install sqlalchemy-migrate
    flask\Scripts\pip install flask-whooshalchemy
    flask\Scripts\pip install flask-wtf
    flask\Scripts\pip install flask-babel
    flask\Scripts\pip install guess_language
    flask\Scripts\pip install flipflop
    flask\Scripts\pip install coverage
