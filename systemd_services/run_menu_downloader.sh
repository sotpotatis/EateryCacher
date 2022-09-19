#run_menu_downloader.py
#Runs the code to download the menu from Eatery.
#Assumes the install position /home/ubuntu/eatery_menu/EateryCacher.
#Feel free to change it to your install position.
echo "Running Eatery menu downloader..."
cd "/home/ubuntu/eatery_menu/EateryCacher/" || exit 1
python3 update_data_from_api.py #Run the menu update code