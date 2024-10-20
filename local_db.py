# For simplificy, we use json as the local DB.
#
# The local DB stores the user data, the contracts metadata and other sensitive
# data.
import json


# Load the data from JSON file
def LoadDatabase():
    with open('local_db.json', 'r') as f:
        return json.load(f)


# Save the data back to the JSON file
def SaveDatabase(db: str):
    print('Updating db with ', db)
    backup = LoadDatabase()
    try:
        with open('local_db.json', 'w') as f:
            json.dump(db, f, indent=4)
    except Exception as e:
        # Restore db on any failures
        with open('local_db.json', 'w') as f:
            json.dump(backup, f, indent=4)
