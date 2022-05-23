# EateryCacher

EateryCacher is a simple HTML-to-human menu converter, which can be used to get lunch data from Eatery Restaurants.

> *Note:* EateryCacher uses unoffical APIs (they are used on Eatery's website, but there is no official documentation available).
Code may be subject to errors and stop work if the API changes. **Note:** Please do not misuse the API, especially since it is unofficial.
> If you are a Eatery representative that is unhappy with this usage of the API, let me know and I will stop crawling data from you as well as make this
repository read-only/archived and/or hidden.

### How the cacher works

The cacher tries to download new data from the Eatery API and saves it onto a file called `cached.json`. This is done by *running the script*
`update_data_from_api.py`. The data can then be served, in parsed format, by running the file `create_server.py`.

*While the server file can be run directly*, it is **not** recommended unless you do some internal testing. In a production environment, use a server like
Gunicorn (it's easy to set up, and Google is absolutely your friend here).

An example command for hosting with Gunicorn is `gunicorn create_server:create_app() --bind=0.0.0.0:80`

### Configuring

See the file `config.ini` for configuration of the EateryCacher.

