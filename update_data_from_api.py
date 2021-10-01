'''update_data_from_api.py
Updates data from the Eatery API and saves it into a data file
'''
from configparser import ConfigParser
from shared_code import CONFIG_FILEPATH, SCRIPT_DIRECTORY, write_json_to_file, read_json_from_file, cached_data_filepath
from fake_useragent import FakeUserAgent
import logging, os, time, requests, json, datetime, pytz
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
menu_ids_to_retrieve = json.loads(downloader_settings["save_menu_ids"])
logger.debug(f"Menus to load: {menu_ids_to_retrieve}")
logger.info("Settings loaded.")


#The first thing to do is to apply the log level
logging.basicConfig(level=logging_settings["level"])

#Load the file cached.json, which stores cached menu data
logger.info("Checking cached data...")
if not os.path.exists(cached_data_filepath): #If the cached data does not exist
    logger.info("Cached data file does not exist. Creating file...")
    write_json_to_file({"cached_menus": {}, "menu_last_updated_at": None}, cached_data_filepath) #Write default JSON
else:
    logger.info("Cached data file exists. Reading file data...")

    #Not performing too many updates is done by checking the menu_last_updated_at key. It is saved as a unix timestamp.
    cached_data_content = read_json_from_file(cached_data_filepath)
    logger.info("Cached data file loaded.")
    logger.info("Checking if an update should be done...")
    update_every_minutes = int(downloader_settings["allow_download_every_minutes"])
    menu_last_updated_at = cached_data_content["menu_last_updated_at"]
    if menu_last_updated_at != None:
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
fake_user_agent = FakeUserAgent()
#Create request headers with the fake user agent
headers = {
    "User-Agent": fake_user_agent.random
}
logger.debug(f"Generated request headers: {headers}")
logger.info("Sending request...")
eatery_request = requests.get("https://api.eatery.se/wp-json/eatery/v1/menues", headers=headers)
logger.info("Request to Eatery sent. Validating...")

#Validate the request
if eatery_request.status_code == 200: #If we get a 200 status code
    logger.info("Status code is 200! Attempting to load JSON...")
    try:
        eatery_request_json = eatery_request.json()
        logger.info("Loaded JSON from response with success.")
    except Exception as e:
        logger.critical("Failed to load JSON from Eatery API! The returned JSON is invalid.", exc_info=True)
        exit(1) #...exit with status code 1 (indicating an error)
else:
    logger.critical(f"Received an unexpected status code from Eatery's API, {eatery_request.status_code}.")
    exit(1) #...exit with status code 1 (indicating an error)

#(if we get here, we have valid JSON data from the Eatery API)
logger.info("JSON data is valid. Loading menus...")


#Iterate through each menu to load and grab its data
for menu_id in menu_ids_to_retrieve:
    if str(menu_id) in eatery_request_json: #If the menu content is available
        logger.info(f"Menu {menu_id} is available. Sending to parser...")
        #Send the menu over to the parser
        menu_parser = MenuParser()
        menu_output = menu_parser.parse(eatery_request_json[str(menu_id)])
        logger.info(f"Got output {menu_output} for menu ID {menu_id}.")
        #Add the menu data to the cached data content
        cached_data_content["cached_menus"][str(menu_id)] = {"menu": menu_output, "last_retrieved_at": datetime.datetime.now(tz=pytz.timezone("Europe/Stockholm")).timestamp()}
        logger.debug("Cached menu content was added in memory.")
    else: #If the content for the menu ID is not available
        logger.warning(f"Menu {menu_id} is not available from Eatery! It will not be included in the current save.")

logger.info("Menu iteration completed. Adding last updated date and saving to file...")
cached_data_content["menu_last_updated_at"] = datetime.datetime.now(tz=pytz.timezone("Europe/Stockholm")).timestamp()
#Save the menu to the file
write_json_to_file(cached_data_content, cached_data_filepath)
logger.info("Data updated to file. All done!")
