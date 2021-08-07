#!/bin/bash

# Vars
HOME=/home/wemakemoneybot

# Only tested on Fedora

# Install dependencies
echo "[+] Install dependencies"
sudo dnf install python3 # NB: There is missing some here!

# Add the user
echo "[+] Adding user 'wemakemoneybot'"
sudo useradd wemakemoneybot

# Move the files from the repo to the new home
echo "[+] Moving files to $HOME"
sudo cp requirements.txt \
    rsi.py \
    wemakemoneybot.py \
    $HOME
sudo chown -R wemakemoneybot: $HOME

# Add the service and enable on boot
echo "[+] Installing and enabling systemd service"
sudo mv etc/systemd/system/wemakemoneybot.service /etc/systemd/system
sudo chown root: etc/systemd/system/wemakemoneybot.service
sudo systemctl enable wemakemoneybot.service

# Install python dependencies
echo "[+] Installing Python dependencies"
sudo su - wemakemoneybot -c "python3 -m pip install -r $HOME/requirements.txt --user"

# TODO: 
# Need to install the following:
# - Selenium
# - Selenium FireFox Driver + place in $PATH

echo "Please ensure you've placed a 'config.py' in $HOME"
echo "Follow the guideline on https://asyncpraw.readthedocs.io/en/stable/tutorials/refresh_token.html#refresh-token for getting the tokens to work"
echo "Once the above is fixed you can start the service by: 'sudo systemctl start wemakemoneybot.service'"
echo ""
echo "~JBT"