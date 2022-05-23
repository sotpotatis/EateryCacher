'''create_server.py
Offers an interface to create a server handling the API.
As in, this file loads the server.py file, sets some configuration variables, and exposes an app
that can be accessed with a WSGI server.
'''

import logging
from configparser import ConfigParser
from shared_code import CONFIG_FILEPATH
from flask import Flask
from flask_cors import CORS

#Logging
logger = logging.getLogger(__name__)

#Set temporary log level, INFO
logging.basicConfig(level=logging.INFO)

#Read the configuration
logger.info("Reading configuration...")
config = ConfigParser()
config.read(CONFIG_FILEPATH)
logger.debug("Config file read.")
server_config = config["server"] #Get server config
#(NOTE: server options below only affects the default Flask server environment)
server_host = server_config["host"]
server_port = int(server_config["port"])
run_in_debug = server_config["debug"]
run_server = config.getboolean("server", "run_using_default_server") #Whether the server should be ran using the default Flask server (load this as a boolean value)
logging_config = config["logging"]
logging_level = int(logging_config["level"])
logger.info("Config read.")

#Set log level requested by user
logging.basicConfig(level=logging_level)

def create_app():
    '''Function for creating an app that can be ran
    using the Flask server (or any other WSGI server).'''
    logger.info("Creating app...")
    #Create a basic app
    app = Flask(__name__)
    CORS(app) #Enable CORS
    """JSON keys are sorted by the code, so we don't want the server to
    sort them."""
    app.config["JSON_SORT_KEYS"] = False #Turn off key sorting
    #Register the server blueprint
    logger.info("Registering blueprint...")
    from server import app as server_blueprint
    #Register server routes
    app.register_blueprint(server_blueprint)
    logger.info("Blueprint registered. Returning app...")
    return app #Return the created app



if run_server == True:
    logger.info("Server should be ran. Running...")
    logger.warning("""WARNING!
    You are running the Flask default server. Only do this in a development
    environment! For production use, use a WSGI server like Gunicorn instead.
    (disable running the server by setting server/run_using_flask in the 
    configuration file to false)""")
    app = create_app()
    app.run(host=server_host, port=server_port, debug=run_in_debug)
else:
    logger.info("Server should not be ran from the server.py script.")
