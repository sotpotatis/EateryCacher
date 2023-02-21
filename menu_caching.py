"""menu_caching.py
Contains helper functions related to caching menus."""
import os, logging, typing, re, shutil

from shared_code import (
    write_json_to_file,
    read_json_from_file,
    get_now,
    CACHED_MENUS_DIRECTORY,
)

logger = logging.getLogger(__name__)

if not os.path.exists(CACHED_MENUS_DIRECTORY):
    logger.info("Creating directory for cached menus...")
    os.mkdir(CACHED_MENUS_DIRECTORY)
else:
    # NOTE
    # Starting 2023-01-13, the menu directory format changed to include the name.
    # This line of code below will automatically apply the migrations.
    # It will only work in the year 2023, so if the year is not 2023, the user have to input
    # the name themselves.
    for menu_id in os.listdir(CACHED_MENUS_DIRECTORY):
        menu_path = os.path.join(CACHED_MENUS_DIRECTORY, menu_id)
        for content in os.listdir(menu_path):
            full_directory_path = os.path.join(
                CACHED_MENUS_DIRECTORY, menu_path, content
            )
            if os.path.isdir(full_directory_path):
                if re.fullmatch("^[0-9]{1,2}$", content):
                    if get_now().year == 2023:
                        logger.info(
                            f"Applying auto migration to directory {full_directory_path}..."
                        )
                        new_directory_name = (
                            f"{content}-2022"  # Add year to the directory name
                        )
                    else:
                        logger.warning(
                            f"""Due to a format change in early 2023 to separate menus by years, some 
                        old menus have to be moved to a new directory.
                        This migration will be automatically applied, however, you have to provide which year the following
                        menu: {full_directory_path} was downloaded at?"""
                        )
                        while True:
                            try:
                                year = int(input("Enter year: "))
                                new_directory_name = f"{content}-{year}"
                            except:
                                logger.warning("Invalid year. Please try again.")
                    new_directory_path = os.path.join(
                        CACHED_MENUS_DIRECTORY, menu_path, new_directory_name
                    )
                    logger.info(
                        f"Auto-migration: move {full_directory_path} to {new_directory_path}"
                    )
                    shutil.move(full_directory_path, new_directory_path)
        logger.info("Check for auto-migrations completed.")


def get_cached_menu_directory(menu_id: str, week: int, year: int) -> str:
    """Gets the directory for a certain menu. Menues are
    stored in the cached directory under their menu ID
    and then their week.

    :param menu_id: The menu ID to get the directory for

    :param week: The week number for the menu.

    :param year: The menu's year."""
    menu_id = menu_id.strip(
        "/"
    )  # Strip / from menu IDs like "/kista_nod" to avoid paths getting messed up
    return os.path.join(CACHED_MENUS_DIRECTORY, f"{menu_id}/{week}-{year}")


def save_cached_menu(menu_id: str, data: dict) -> None:
    """Saves cached menu data for a week."""
    logger.info(f"Saving menu for {menu_id}...")
    week_number = data["menu"]["week_number"]
    year_number = get_now().year
    # Get path for menu
    cached_menu_directory = get_cached_menu_directory(menu_id, week_number, year_number)
    root_directory_id = os.path.dirname(cached_menu_directory)
    menu_data_file_path = os.path.join(cached_menu_directory, "data.json")
    # Create directories if not exists
    if not os.path.exists(root_directory_id):
        logger.info(f"Creating directory for menu {menu_id}...")
        os.mkdir(root_directory_id)
    if not os.path.exists(cached_menu_directory):
        logger.info(f"Creating directory for menu {menu_id}, week {week_number}...")
        os.mkdir(cached_menu_directory)
    # Compare old menu data to save if Eatery saves their menu. It's cool to track changes!
    if os.path.exists(menu_data_file_path):
        logger.info("Menu data already exists. Comparing for differences...")
        menu_data = read_json_from_file(menu_data_file_path)
        if menu_data["menu"] != data["menu"]:
            logger.info("Got changed menu data. Pushing new menu data...")
            if "previous_revisions" not in menu_data:
                menu_data["previous_revisions"] = []
            menu_data["previous_revisions"].append(
                {
                    "revision_number": len(menu_data["previous_revisions"]) + 1,
                    "change_discovered_at": get_now().timestamp(),
                    "previous_data": menu_data["menu"],
                }
            )
            logger.info("Added information about differences.")
    else:
        logger.info("Menu data will be new.")
        menu_data = {}
    # Update menu data
    menu_data["menu"] = data["menu"]
    menu_data["menu_id"] = data["menu_id"]
    menu_data["last_retrieved_at"] = get_now().timestamp()
    # Write to file
    logger.info(f"Writing menu data for week {week_number} to file...")
    write_json_to_file(menu_data, menu_data_file_path)
    logger.info(f"Menu data written to {menu_data_file_path}.")


def get_cached_menu(
    menu_id: str, week_number: int, year_number: int
) -> typing.Optional[dict]:
    """Gets the cached menu for a certain ID and week.

    :param menu_id: The menu ID to retrieve.

    :param week_number: The week number to retrieve.

    :param year_number: The year number to retrieve data from.

    :returns: The menu data if the menu was found, None if it
    can't be found."""
    cached_menu_directory = get_cached_menu_directory(menu_id, week_number, year_number)
    # Check if menu ID is digit.
    # If the requested menu ID is a string, we can simply retrieve it right away.
    # If not, we have to try to find the menu string that belongs to the menu ID.
    menu_id_is_digit = menu_id.isdigit()
    logger.info(f"Getting menu for ID {menu_id}, week {week_number}")
    if not menu_id_is_digit:  # Is string - return menu right away
        logger.debug("Is not digit - returning right away if exists.")
        # Validate that files exist and then save them
        if os.path.exists(cached_menu_directory):
            menu_data_file_path = os.path.join(cached_menu_directory, "data.json")
            if os.path.exists(menu_data_file_path):
                return read_json_from_file(menu_data_file_path)
    else:  # Is digit - iterate over all menus until an appropriate one is found for the week
        logger.debug("Is digit - iterating over all menus...")
        for menu in os.listdir(CACHED_MENUS_DIRECTORY):
            if str(week_number) in os.listdir(
                os.path.join(CACHED_MENUS_DIRECTORY, menu)
            ):
                menu_data_file_path = os.path.join(
                    f"{CACHED_MENUS_DIRECTORY}/{menu}/{week_number}", "data.json"
                )
                if os.path.exists(menu_data_file_path):
                    menu_content = read_json_from_file(menu_data_file_path)
                    if menu.isdigit() and menu == menu_id:
                        return menu_content
                    elif "menu_id" in menu_content and menu_content["menu_id"] == int(
                        menu_id
                    ):
                        return menu_content
    return None
