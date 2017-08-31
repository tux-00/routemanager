# routemanager
Manage routes to deal with overlapping networks.

![Imgur](http://i.imgur.com/Eui2PMa.png)

## Use case
Suppose you need to connect to multiple clients/networks configured with the same network IP for any reason.
This app provide a way to easily add/remove routes to bypass overlapping.

routemanager provide a way to easily manage routes.

**Warning:** as routemanager is changing routes, be carefull with this app.

## Installation
```
virtualenv -p python3 env
source env/bin/activate
pip3 install -r requirements.txt
pip3 install --editable .
```

## Configuration
Open the file `routemanager/routemanager/routemanager.py` and edit the *app.config.update* dict to match your configuration.

*IF_VPN* is the most important configuration, you need to provide the name of the interface to manage. If the interface doesn't exist, the app will raise an exception.

## Run
To run the app just type `routemanager` in your terminal.

**Warning:** by default the app is in debug mode and listen on `0.0.0.0`.

Edit `bin/routemanager` to change listen address and debug option.

## Reset database
```
export FLASK_APP=routemanager
flask initdb
```
