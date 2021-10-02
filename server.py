'''server.py
Provides an API interface/server that allows one to retrieve menu data.
Uses Flask as a backend.
'''
from flask import Blueprint, jsonify, send_from_directory
from shared_code import read_json_from_file, cached_data_filepath, EATERY_KISTA_NOD_MENU_ID
from menuparser import day_names_to_json_keys
from http import HTTPStatus
import logging, datetime, pytz

#Logging
logger = logging.getLogger(__name__)

app = Blueprint(__name__, "server")

def generate_api_response(status, content, status_code=200):
    '''Function for generating an API response following the response format
    (status and content).

    :param status: The status as a text.

    :param content: The request content (as a dictionary)

    :param status_code: The status code.'''
    logger.info(f"Creating API response with status {status}, status code {status_code}...")
    response = content
    response["status"] = status
    response["status_code"] = status_code
    return response #Return the response

def generate_api_error_response(error_message, status_code):
    '''Function for generating an API error.

    :param error_message: The error message to return.

    :param status_code: The status code to return.'''
    return generate_api_response("error", {"message": error_message}, status_code)

def generate_api_response_for(menu_id, week_number, day_number=None):
    '''Generates an API response for a specific menu ID and a
    specific week number.'''
    logger.info(f"Generating API response for menu id {menu_id}, week day {week_number}...")
    #Grab menu data
    menu_data = read_json_from_file(cached_data_filepath)
    logger.debug(f"Menu data: {menu_data}")
    if str(menu_id) in menu_data["cached_menus"]:
        logger.info("Menu is available. Checking if requested week is available...")
        requested_menu = menu_data["cached_menus"][str(menu_id)]
        if requested_menu["menu"]["week_number"] != week_number and requested_menu["menu"]["week_number"] != None:
            logger.info("Menu is not available.")
            return generate_api_error_response("Menu for requested week is not available.", HTTPStatus.NOT_FOUND)
        else:
            logger.info("Menu is available. Returning response...")
            #If a specific day hasn't been requested...
            if day_number == None:
                return generate_api_response("success", requested_menu) #...return the full menu
            else:
                logger.debug("Custom day has been specified! Checking and returning...")
                if day_number > len(day_names_to_json_keys): #If the passed day number is not in the list of keys (there should be error-checking for this implemented in the server, so unless this function is called externally, this error should not be triggered)
                    logger.warning("Invalid length passed!")
                    return generate_api_error_response("Unknown day number passed.", HTTPStatus.BAD_REQUEST)
                else:
                    requested_day_key = list(day_names_to_json_keys.values())[day_number-1]
                    logger.info(f"Requested day: {requested_day_key}")
                logger.debug("Checking for existence of the requested day..")
                if requested_day_key not in requested_menu["menu"]["days"]:
                    logger.info("Custom day is not available!")
                    return generate_api_error_response("Requested day is not available.", HTTPStatus.BAD_REQUEST)
                else:
                    logger.info("Custom day is available!")
                    return generate_api_response("success", {requested_menu["menu"]["days"][requested_day_key]}) #Get the menu for that day

    else:
        logger.info("Menu is not available. Returning error response...")
        return generate_api_error_response("Menu ID not available.", HTTPStatus.NOT_FOUND)

#API endpoints
@app.route("/api/")
def api():
    '''General API. Returns the Eatery Kista Nod menu
    for the current week.'''
    logger.info("Got a request to the general API! Generating response...")
    #Get current week
    current_week = datetime.datetime.now(tz=pytz.timezone("Europe/Stockholm")).isocalendar()[1]
    logger.info(f"Current week: {current_week}")
    #Generate response
    response = generate_api_response_for(EATERY_KISTA_NOD_MENU_ID, current_week)
    logger.info(f"Response retrieved: {response}. Returning...")
    return jsonify(response), response["status_code"] #Return the response

@app.route("/api/<int:menu_id>/<int:week_number>")
def specific_api(menu_id, week_number):
    '''Specific API. Allows one to specify the menu ID and the week number.'''
    logger.info("Got a request to the specific API! Generating response...")
    #Generate response
    response = generate_api_response_for(menu_id, week_number)
    logger.info(f"Response retrieved: {response}. Returning...")
    return jsonify(response), response["status_code"] #Return the response


@app.route("/api/<int:menu_id>/<int:week_number>/<int:day_number>")
def specific_day_api(menu_id, week_number, day_number):
    '''Specific day API. Allows one to specify the menu ID, the week number, and the day ID to retrieve.'''
    logger.info("Got a request to the specific day API! Generating response...")
    #Validate the day ID
    if day_number < 1 or day_number > 7:
        logger.info(f"Invalid day number sent ({day_number}). Returning error...")
        return generate_api_error_response("Invalid day number (must be 1-7)", HTTPStatus.BAD_REQUEST), HTTPStatus.BAD_REQUEST
    logger.debug("Day number is valid. Generating response...")
    #Generate response
    response = generate_api_response_for(menu_id, week_number, day_number)
    logger.info(f"Response retrieved: {response}. Returning...")
    return jsonify(response), response["status_code"] #Return the response
