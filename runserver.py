#!/usr/bin/env python3

import json
from showmanager.views import app

# Load settings file    
with open('settings.json') as fp:
    settings = json.load(fp)

app.secret_key = settings['secret_key']
    
# Run the flask app in debug mode
app.run(debug=True)
