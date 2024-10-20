# A middle layer DB between walrus and user.  It supports the version control
# of the undelrying blob IDs.
#
# Every store, queyr and fetch operations go through this lib.
import os
import subprocess
import json

import model
import local_db
import utils

PATH_TO_WALRUS_CONFIG = os.path.join(os.getcwd(), '../../client_config.yaml')
PATH_TO_WALRUS = 'walrus'


# Stores the data to Walrus DB.
# Returns the Version object that was created/updated.
def UploadFileOnVersion(filepath: str, client_id: str,
                        version_id: str) -> model.Version:
    print(
        f'Calling UploadFileOnVersion({filepath}, {client_id}, {version_id})')

    # Load the local DB where version information is stored
    db = local_db.LoadDatabase()
    print("Loaded DB:", db)

    # Find the client using the client_id
    client = utils.GetClientById(client_id)
    print('Client found:', client)

    # Find the base version by searching through the contracts and their versions
    based_on_version = None
    for contract in client.contracts:
        for version in contract.versions:
            if version.blob_id.bid == version_id:
                based_on_version = version
                break
        if based_on_version:
            break

    if not based_on_version:
        raise ValueError(
            f'Base version with version_id {version_id} not found.')

    print('based_on_version=', based_on_version)

    # Upload file to Walrus and get the new BlobID
    try:
        store_json_command = f"""{{ "config" : "{PATH_TO_WALRUS_CONFIG}",
          "command" : {{ "store" :
          {{ "file" : "{filepath}", "epochs" : 2  }}}}
        }}"""
        print(f'Running command: {store_json_command}')
        result = subprocess.run(
            [PATH_TO_WALRUS, "json"],
            text=True,
            capture_output=True,
            input=store_json_command,
        )

        # Ensure the subprocess ran successfully
        if result.returncode != 0:
            raise RuntimeError(
                f"Error storing file in Walrus: {result.stderr}")

        print(result.stdout.strip())

        # Parse the JSON result
        json_result_dict = json.loads(result.stdout.strip())

        # Extract the BlobID from the Walrus response
        newly_created = json_result_dict.get("newlyCreated", None)
        if not newly_created:
          print("Already exist. skip ")
          already_certified = json_result_dict.get("alreadyCertified", None)
          bid = already_certified.get("blobId")
          return model.Version(model.BlobID(bid, 0), None, None, "Already eixsts")

        new_blob_id_str = newly_created.get("blobObject").get("blobId")

        if not new_blob_id_str:
            raise ValueError("No BlobID found in Walrus response")

        print(f'New BlobID {new_blob_id_str}')

        # Create a BlobID object from the returned blob ID
        new_blob_id = model.BlobID(
            bid=new_blob_id_str, timestamp=0)

        # Create a new Version object
        new_version = model.Version(
            blob_id=new_blob_id,
            initial_blob_data=based_on_version.initial_blob_data,
            previous_versions=based_on_version.previous_versions +
            [based_on_version.blob_id],
            alias=based_on_version.alias)

        # Add the new version to the corresponding contract
        for contract in client.contracts:
            if based_on_version in contract.versions:
                contract.versions.append(new_version)
                break

        # Replace the old client with the updated client in the database
        db['clients'] = [c if c['client_id'] != client_id else client.to_dict() for c in db['clients']]


        # Save the updated database
        local_db.SaveDatabase(db)
        print(f"New version stored with BlobID: {new_blob_id_str}")

    except Exception as e:
        print(f"Error during upload: {e}")
        raise

    return new_version


# Fetch data
def FetchFileByVersion(version: model.Version) -> bytes:
    print(f'Fetching file for version with BlobID: {version.blob_id.bid}')

    # Fetch the data from Walrus based on the blob_id in the version
    file_data = walrus.read(
        version.blob_id.bid)  # Assuming walrus.read fetches the file by BlobID

    return file_data


# Queries the data by blobid and query options.
# Returns a list of the Versions that match the query criteria.
def QueryVersions(version: model.Version,
                  query_options: model.QueryOptions) -> list[model.Version]:
    print(f'Querying versions based on options: {query_options}')

    # Load the local DB where version information is stored
    db = local_db.LoadDatabase()

    # Filter versions by timestamp (before/after)
    if query_options.query_by_time:
        before = query_options.query_by_time.before
        after = query_options.query_by_time.after
        versions_by_time = [
            v for v in db['versions']
            if (before is None or v.blob_id.timestamp <= before) and (
                after is None or v.blob_id.timestamp >= after)
        ]
    else:
        versions_by_time = db['versions']

    # Filter versions by incremental version number
    if query_options.query_by_version is not None:
        versions_by_version = [
            v for v in versions_by_time
            if v.blob_id.version == query_options.query_by_version
        ]
    else:
        versions_by_version = versions_by_time

    # (Optional) You can add logic for `query_description` using AI-based filtering or keyword matching

    # Return the filtered versions
    return versions_by_version
