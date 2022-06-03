'''shared_code.py

Some shared code and constants between the server and the retriever.

'''
import os, logging, json, datetime, pytz

#Set up logging by creating a logger
logger = logging.getLogger(__name__)

#Constants
EATERY_KISTA_NOD_MENU_ID = "/kista-nod" #The Eatery Kista nod menu ID

#Grab paths
SCRIPT_FILEPATH = os.path.realpath(__file__)
SCRIPT_DIRECTORY = os.path.dirname(SCRIPT_FILEPATH)
CONFIG_FILEPATH = os.path.join(SCRIPT_DIRECTORY, "config.ini")
cached_data_filepath = os.path.join(SCRIPT_DIRECTORY, "cached.json")
statistics_data_file_path = os.path.join(SCRIPT_DIRECTORY, "statistics.json")

def read_json_from_file(file_path):
    '''Function for reading JSON from a file. Returns the file content as a dictionary.

    :param file_path: The path of the file to load'''
    logger.debug(f"Reading JSON from {file_path}...")
    return json.loads(open(file_path, "r").read())

def write_json_to_file(data_to_write, file_path):
    '''Function for writing JSON to a file. The file can be new or old.

    :param data_to_write: The data to write as a dict (must be JSON-serializable)

    :param file_path: The file path to write to.'''
    logger.debug(f"Writing data {data_to_write} as JSON to {file_path}...")
    #Open the file and write the new data
    with open(file_path, "w") as data_file:
        data_file.write(json.dumps(data_to_write, indent=True))

def get_now():
    '''Retrieves the current time in Stockholm, Sweden timezone.'''
    return datetime.datetime.now(tz=pytz.timezone("Europe/Stockholm"))
