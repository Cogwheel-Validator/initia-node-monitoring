# Initia Node Monitoring

This Python script checks your node and compares it with public RPCs. It does this by going through the config.yml file, checking their status, collecting all their heights, and picking the highest value to compare with your node height. If your node stops working or starts falling behind, it will send a notification using Telegram. This script is designed to be easy to use for everyone.

## A small warning before you proceed

This script has had some limited testing so no one from Cogwheel or any other RPC providers used for this
script will be held accountable if your node starts to miss blocks or if the script does for some unknown 
reason stops working.

## Installation 
This script has been tested using Python version 3.11 but it should work from Python 3.9 and above. Make a clone of this repo by using this command:

```
git clone https://github.com/Cogwheel-Validator/initia-node-monitoring.git
```

Then go into directory and install all of the necessary libraries:

```
cd initia-node-monitoring/
pip install -r requirements.txt
```

## Configuration

After the installation is complete head to the config directory and make changes to the config.yml and telegram.yml

```
cd config/
vim config.yml #or use any other text editor like nano, nvim etc...
```

The only change here you need to make is to change URL under the node. If you use the default settings
for the RPC you can actually leave it as it is. Optionally you can add more RPCs if you want but the current 
list should be sufficient. You can also adjust alert levels if you want but we do not recommend that you 
change anything unless you know what you are doing.

For the telegram.yml file, you will need to create a bot and a chat, which you will then insert into telegram.yml. For more information on creating a bot, see [this guide](https://www.directual.com/lesson-library/how-to-create-a-telegram-bot) and how to find [chat-id](https://medium.com/@2mau/how-to-get-a-chat-id-in-telegram-1861a33ca1de) see this guide.

## Run the script

Return to the main directory if you are still inside config and run this command:

```
python3 main.py
```

It will run the python script. You will be able to see logs. To stop the script press CTRL + C. If you want
the script to run in the background you can make a systemd service file which will run in the background.

```
sudo tee /etc/systemd/system/initia-monitoring.service > /dev/null <<EOF
[Unit]
Description=initia Node monitoring
After=network.target

[Service]
ExecStart=/usr/bin/python3 $HOME/initia-node-monitoring/main.py
WorkingDirectory=$HOME/initia-node-monitoring
Restart=always
RestartSec=5s
User=$USER
Environment="PYTHONUNBUFFERED=1"
 
[Install]
WantedBy=multi-user.target
EOF
```
Be sure to set it to the place where you cloned the repository.

After that make sure it to enable the service and you can start the service
```
sudo systemctl enable initia-monitoring.service
# start the service and monitor it
sudo systemctl start initia-monitoring.service && sudo journalctl -fu initia-monitoring -o cat
```

## Known bugs and errors

1. Sometimes some RPC nodes might get an error starting with 4xx or 5xx. This is mostly dependent on
the one that provides this service and there is nothing you can do on your side.

