import json

# Load configuration from the JSON file
with open('config.json') as config_file:
    config = json.load(config_file)

# Get the path to the database
DB_PATH = config["database"]["path"]
