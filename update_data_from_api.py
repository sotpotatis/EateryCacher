'''update_data_from_api.py
Updates data from the Eatery API and saves it into a data file
'''
from configparser import ConfigParser
from shared_code import CONFIG_FILEPATH, write_json_to_file, read_json_from_file, status_data_filepath, get_now
from fake_useragent import FakeUserAgent
import logging, os, time, requests, json, datetime, pytz, menu_caching
from menuparser import MenuParser

#Set up logging by creating a logger
logger = logging.getLogger(__name__)

#Load the configuration file
logger.info("Loading configuration file...")
config = ConfigParser()
config.read(CONFIG_FILEPATH) #Read the configuration filepath
logger.info("Configuration file loaded. Loading parameters...")

#Load the subsections for the downloader and for logging from the configuiration file
downloader_settings = config["downloader"]
logging_settings = config["logging"]
#Load which menu IDs to retrieve at this point, since this should be a list and therefore has an extra risk of giving an error
if "save_menu_ids" in downloader_settings:
    if "save_menus" not in downloader_settings:
        logger.critical("The save_menu_ids settings has been deprecated. Please use \"save_menus\" instead. See the example configuration file for more information.")
        exit(1)
    else:
        logger.warning("The save_menu_ids settings has been deprecated. Please use \"save_menus\" instead. See the example configuration file for more information.")
menus_to_load = json.loads(downloader_settings["save_menus"])
logger.debug(f"Menus to load: {menus_to_load}")
logger.info("Settings loaded.")


#The first thing to do is to apply the log level
log_level = int(logging_settings["level"])
logging.basicConfig(level=log_level)

#Load the file status.json, which stores when menus were last updated
logger.info("Checking cached data...")
if not os.path.exists(status_data_filepath): #If the cached data does not exist
    logger.info("Cached data file does not exist. Creating file...")
    status_content = {"menus_last_updated_at": None}
    write_json_to_file(status_content, status_data_filepath) #Write default JSON
else:
    logger.info("Cached data file exists. Reading file data...")

    #Not performing too many updates is done by checking the menus_last_updated_at key. It is saved as a unix timestamp.
    status_content = read_json_from_file(status_data_filepath)
    logger.info("Cached data file loaded.")
    logger.info("Checking if an update should be done...")
    update_every_minutes = int(downloader_settings["allow_download_every_minutes"])
    menu_last_updated_at = status_content["menus_last_updated_at"]
    if menu_last_updated_at is not None:
        seconds_since_last_download = time.time() - menu_last_updated_at #Get the amount of seconds since last download
        minutes_since_last_download = seconds_since_last_download / 60 #Calculate the amount of minutes elapsed since the last download
        logger.info(f"Minutes elapsed since last download: {minutes_since_last_download} minutes.")
        if minutes_since_last_download < update_every_minutes: #If the script is being run too often.
            logger.critical("It has not elapsed the required amount of time before an update should be performed again! The script will exit.")
            exit(1) #...exit with status code 1 (indicating an error)
    else:
        logger.debug("Menu update data is not available (is None). Downloading menu...")

#(if we get here, we are good too go with an update)
logger.info("An update should be performed. Downloading data from Eatery...")

#Create a fake user-agent (yes, this is a bit fishy, but this is done to get past any possible user agent filters, since at least we're using the data for good purpose!)
try:
    fake_user_agent = FakeUserAgent()
    #Create request headers with the fake user agent
    user_agent = fake_user_agent.random
except Exception as e:
    logger.warning(f"Fake user agent failed with exception {e}! Using bypass.", exc_info=True)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0"
headers = {
    "User-Agent": user_agent
}
logger.debug(f"Generated request headers: {headers}")
logger.info("Sending request...")
eatery_eateries_request = requests.get("https://api.eatery.se/wp-json/eatery/v1/eateries", headers=headers)
eatery_menues_request = requests.get("https://api.eatery.se/wp-json/eatery/v1/menues", headers=headers)
logger.info("Requests to Eatery sent. Validating...")

#Validate the request
if eatery_menues_request.status_code == eatery_eateries_request.status_code  == 200: #If we get a 200 status code
    logger.info("Status code is 200! Attempting to load JSON...")
    try:
        eatery_eateries_request_json = eatery_eateries_request.json()
        eatery_menues_request_json = eatery_menues_request.json()
        logger.info("Loaded JSON from response with success.")
    except Exception as e:
        logger.critical("Failed to load JSON from Eatery API! The returned JSON is invalid.", exc_info=True)
        exit(1) #...exit with status code 1 (indicating an error)
else:
    logger.critical(f"Received an unexpected status code from Eatery's API, {eatery_menues_request.status_code}.")
    exit(1) #...exit with status code 1 (indicating an error)

#(if we get here, we have valid JSON data from the Eatery API)
logger.info("JSON data is valid. Loading menus...")


#Iterate through each menu to load and grab its data
for menu_name in menus_to_load:
    if not menu_name.startswith("/"): #Menu paths begin with a forward slash (for example /kista-nod). Therefore, document and add it in case someone forgot to do it :)
        logger.warning(f"Desiring a slash (/) in front of the menu path \"{menu_name}\". To supress this warning, change your configuration file from {menu_name} to /{menu_name}.")
    #Get the latest menu from the list of Eateries, This extra step has been added if Eatery changes their menu ID
    if menu_name in eatery_eateries_request_json and "lunchmeny" in eatery_eateries_request_json[menu_name]["menues"]: #Check that menu is available and that a lunch menu is available from it
        menu_id = eatery_eateries_request_json[menu_name]["menues"]["lunchmeny"]
        if str(menu_id) in eatery_menues_request_json: #If the menu content is available
            logger.info(f"Menu {menu_id} is available. Sending to parser...")
            #Send the menu over to the parser
            menu_parser = MenuParser()
            menu_output = menu_parser.parse(eatery_menues_request_json[str(menu_id)])
            logger.info(f"Got output {menu_output} for menu ID {menu_id}.")
            #Add the menu data to the cached data content
            menu_data = {"menu": menu_output, "menu_id": menu_id, "last_retrieved_at": get_now().timestamp()}
            menu_caching.save_cached_menu(menu_name.strip("/"), menu_data)
            logger.debug("Cached menu content was saved.")
        else: #If the content for the menu ID is not available
            logger.warning(f"Menu {menu_id} is not available from Eatery! It will not be included in the current save.")
    else:
        logger.warning(f"Menu for {menu_name} is not available from Eatery! It will not be included in the current save.")

logger.info("Menu iteration completed. Adding last updated date and saving to file...")
status_content["menu_last_updated_at"] = datetime.datetime.now(tz=pytz.timezone("Europe/Stockholm")).timestamp()
#Save the menu to the file
write_json_to_file(status_content, status_data_filepath)
logger.info("Data updated to file. All done!")
