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
 * on Linux you should probably run `python3 -m venv flask`
4. While still in the root of the repo, run the following commands. (Most of them are likely not necessary, but they're adopted from a tutorial, it works and it's a virtualenv anyway.)
 * on Linux: replace `flask\Scripts\pip` with `flask/bin/pip`
```
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
    flask\Scripts\pip install numpy
```

5. The environment should be ready now.

### Moving configuration files
At this point, you have everything you need to run the app, just in the wrong place. Let's fix that.
1. Copy all config files in the `install/` folder into the root of the repository.
2. Change the copies according to your liking. You don't have to, but you might want to.
 * Changing `SECRET_KEY` in `config.py` is probably a good idea.
 * Changing the IP address/port in `run.py` might be necessary.
3. If you're on Linux, you need to properly chmod the `run.py` file with the following
 * `chmod a+x run.py`

### Running the server
At this point, you should be able to run the server like this:

    cd C:\Repa\scrapknight
    flask\Scripts\python run.py

or on Linux:

    cd ~/repa/scrapknight
    ./run.py

Once you're running, the website should be visible on [http://localhost:5010/](http://localhost:5010/) unless you changed the IP address/port in the configs.

Have fun!
