![ScrapKnight logo](app/static/img/logo_github.png)

Magic scrapper/multitool.

## Installation of dev environment

### Prerequisities
We assume you have a working Anaconda 3 installation. If you don't, we leave it to you to install all the dependencies you might be missing into your Python distribution.

### Clone this repo
Add this repository to your favourite git client. Let's assume you put it into `C:\Repa\scrapknight`.

### Setting up a virtual environment

1. Open up terminal
2. run `conda env create -f scrap.yml`
 * this should create a new conda environment with all the dependencies necessary
 * NOTE: `imagehash` requires `pywavelets` which currently doesn't have a pre-compiled version for Python 3.6. You can either use Python 3.5 (not tested, but simpler) or it will try to build while creating the environment. This however requires *Visual C++ Build Tools* (external install, link will show in pip error log).
 * If you run into mistakes, you can remove the environment by running `conda remove --name scrap --all`
3. Install MySQL version >= 5.6.
 * For example from here: [http://dev.mysql.com/downloads/mysql/](http://dev.mysql.com/downloads/mysql/)
 * Feel free *to install as a service*, all you need is "MySQL server" and "MySQL Notifier" is also pretty useful
4. You will probably need to create an empty database called `scrapknight`.
5. The environment should be ready now. You can now enter the new Python conda environment by typing
 * Windows: `activate scrap` / `deactivate scrap`
 * Linux: `source activate scrap` / `source deactivate scrap`

### Moving configuration files
If you have done everything correctly (and a little more), you have everything you need to run the app, just in the wrong place. Let's fix that.

1. Copy the `install/config.py` file into the `app` folder.
2. Edit the configuration according to your liking. You don't have to, but you might want to.
 * Changing `SECRET_KEY` is probably a good idea.
 * Changing the database login information might be required for the site to work.
 * Changing the IP address/port in `RunConfig` might be necessary.
 * Changing the `CLIENT_ID` and `CLIENT_SECRET` to the appropriate values.


### Create SSL certificates
Start python console in repository root and run

    from werkzeug.serving import make_ssl_devcert
    make_ssl_devcert('app/ssl', host='localhost')

### Filling the database
To gather the data and fill the database, run:

    (scrap) cd C:\Repa\scrapknight
    (scrap) python build.py

or on Linux:

    (scrap) cd ~/repa/scrapknight
    (scrap) ./build.py


### Running the server
At this point, you should be able to run the server like this:

    (scrap) cd C:\Repa\scrapknight
    (scrap) python run.py

or on Linux:

    (scrap) cd ~/repa/scrapknight
    (scrap) ./run.py

Once you're running, the website should be visible on [http://localhost:5010/](http://localhost:5010/) unless you changed the IP address/port in the configs.

Have fun!
