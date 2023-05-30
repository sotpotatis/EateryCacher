"""menuparser.py
Parses the menu content from an Eatery menu (as HTML) into a human-readable JSON that is
structured by day. Nice, right?
"""
import logging, re
from bs4 import BeautifulSoup

# Constants
day_names_to_json_keys = {
    "Måndag": "monday",
    "Tisdag": "tuesday",
    "Onsdag": "wednesday",
    "Torsdag": "thursday",
    "Fredag": "friday",
    "Lördag": "saturday",
    "Söndag": "sunday",
}
special_features = {
    "Sweet Tuesday": "sweet_tuesday",
    "Fruity Wednesday": "fruity_wednesday",
    "Pancake Thursday": "pancake_thursday",
    "Burger Friday": "burger_friday",
}
week_days_id_list = list(day_names_to_json_keys.values())
known_footer_phrases = [
    re.compile(
        "(.*)Eaterykortet*(.*)"
    ),  # Alternativt regex: (((L|l)unch){0,} *[0-9]{0,} *kr *)(med *){0,}Eaterykortet(.*) (mindre kompakt)
    re.compile("(.*)ingår(.*)"),
    re.compile("(.*)Rädda maten!(.*)"),
    re.compile("(.*)Om vi får över mat från lunchen(.*)"),
    re.compile(r"(.*)Endast \d+kr, bra för miljön och för din plånbok.(.*)"),
    re.compile("(.*)Early Bird(.*)"),
    re.compile("(.*)L = Laktos"),
    re.compile("(.*)G = Gluten"),
    re.compile("(.*)N = Nötter"),
    re.compile("(.*)S = Skaldjur"),
    re.compile("(.*)F = Fisk"),
    re.compile("(.*)allergier(.*)"),
]  # Known phrases that are in the bottom of the Eatery menu
week_menu_title_regex = re.compile(
    "([\D]*)([0-9]{1,2})([\D]*)"
)  # Regex for getting the week number from a title.
# Logging
logger = logging.getLogger(__name__)


class MenuParser:
    """A parser for parsing a menu."""

    def __init__(self):
        """Initialization function. Does not require any arguments."""
        pass

    def parse(self, menu_content):
        """Function for parsing a menu. Takes the JSON value from Eatery's API (loaded as a dict),
        and converts it into a human-readable, JSON-serializable, dictionary.

        :param menu_content: The JSON value from Eatery's API (loaded as a dict)"""
        # Get the menu string
        menu_string = menu_content["content"]["content"]
        menu_title = menu_content["content"]["title"]
        menu_url = (
            "https://eatery.se/" + menu_content["uri"].strip("/")
            if "uri" in menu_content
            else None
        )
        # Extract week from title
        logger.info("Attempting to extract week from menu title...")
        menu_week_match = re.fullmatch(week_menu_title_regex, menu_title)
        if menu_week_match:
            logger.debug("Week number match found. Grabbing group...")
            menu_week = int(menu_week_match.group(2))
            logger.info(f"Week for menu grabbed. (Week {menu_week})")
        else:
            logger.warning(f"Week number not found for title {menu_title}!")
            menu_week = None
        menu_footer = (
            menu_content["content"]["footer"] if "footer" in menu_content else []
        )
        # Parse footer
        if len(menu_footer) > 0:
            if type(menu_footer) == list:
                logger.debug("Footer is list. Joining...")
                menu_footer = "\n".join([item["text"] for item in menu_footer])
            else:
                logger.debug("Footer type is not list.")
        else:  # If no footer is present
            logger.debug("No footer is present.")
            menu_footer = None
        logger.info(f"Extracting content of {menu_string}...")
        menu_metadata = {
            "title": menu_title,
            "week_number": menu_week,
            "url": menu_url,
        }  # The menu data result
        result = {}
        # Get raw text with help of the wonderful BeautifulSoup
        soup = BeautifulSoup(menu_string, "html.parser")
        raw_menu_text = soup.get_text()
        logger.debug(f"Raw menu text: {raw_menu_text}. Splitting...")
        raw_menu_lines = raw_menu_text.splitlines()
        # Iterate through lines
        current_day = None
        for row in raw_menu_lines:
            logger.debug(f"Parsing row content {row}...")
            found_day = None
            for day, day_id in day_names_to_json_keys.items():
                if day.lower() in row.lower():  # If a day was found
                    logger.info(f"Found data for day {day}!")
                    found_day = current_day = day_id
                    result[found_day] = {
                        "day_name": {"swedish": day, "english": day_id.capitalize()},
                        "dishes": [],
                        "special_features": {  # A list of special features, like "Sweet Tuesday", when dessert is served
                            "sweet_tuesday": False,
                            "fruity_wednesday": False,
                            "pancake_thursday": False,
                            "burger_friday": False,
                        },
                    }
                    break
            if (
                found_day == None and current_day != None
            ):  # If no day was found in this line, add the menu content to another line
                logger.debug("Adding to previous day...")
                # Look for special features (when dessert is served, for example)
                logger.debug("Looking for special features...")
                for special_feature, special_feature_key in special_features.items():
                    if special_feature in row:
                        logger.info(f"Found {special_feature}!")
                        result[current_day]["special_features"][
                            special_feature_key
                        ] = True  # Mark that an attribute was found
                    else:
                        logger.debug(
                            f"{special_feature} was not found for {current_day} (row content: {row})"
                        )
                logger.debug(
                    f"Special features for {current_day}: {result[current_day]['special_features']}"
                )  # Log found special features for the day
                if len(row) > 1:
                    if (
                        any(re.fullmatch(regex, row) for regex in known_footer_phrases)
                        is False
                    ):  # If no known footer phrases has been found
                        row = row.strip()  # Trim whitespace from row
                        result[current_day]["dishes"].append(
                            row
                        )  # Add the row to the list of dished for the day
                    else:
                        logger.debug(f"{row} is an expected/known footer phrase.")
                        if menu_footer is None:  # Add footer if not added already
                            menu_footer = ""
                        menu_footer += f"\n{row}"
            else:
                logger.info("Nothing should be added to the previous row.")
        # Sort result so that it starts with monday and ends with the last day that a menu item is available for.
        logger.info("Sorting result...")

        def sort_by_day(day):
            """Function for sorting a dict's keys based on days.
            Returns a sorted list of the keys."""
            return week_days_id_list.index(day)

        sorted_result_keys = list(result.keys())  # Sort available keys
        sorted_result_keys.sort(key=sort_by_day)
        result = {key: result[key] for key in sorted_result_keys}
        # Add the result to the menu metadata
        menu_metadata["days"] = result
        # Add footer to the menu metadata
        menu_metadata["footer"] = menu_footer
        logger.debug(f"Final data: {result}.")
        logger.info(f"Final metadata: {menu_metadata}.")
        return menu_metadata  # Return the result
