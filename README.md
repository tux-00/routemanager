# routemanager
Manage routes to deal with overlapping networks.

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

**Warning:** the app is by default in debug mode.
