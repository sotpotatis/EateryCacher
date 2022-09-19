#!/bin/bashF
#start_menu_api.sh
#Starts the server to run the menu API.
#Assumes the install position /home/ubuntu/eatery_menu/EateryCacher.
#Feel free to change it to your install position.
echo "Running menu API..."
cd /home/ubuntu/eatery_menu/EateryCacher || exit 1
gunicorn create_server:app -b "127.0.0.1:80" #Run the server (using gunicorn)