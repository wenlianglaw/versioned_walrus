import os
import sys
import sign_ocntract_model
import local_db

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import model


def GetClientById(client_id: str) -> sign_ocntract_model.Client:
    """
    Retrieves a client object by its client ID from the local database.
    """
    # Load the local database
    db = local_db.LoadDatabase()

    # Search for the client in the database
    for client_data in db['clients']:
        if client_data['client_id'] == client_id:
            # Create a sign_ocntract_model.Client object from the client data
            client = sign_ocntract_model.Client(
                client_id=client_data['client_id'],
                name=client_data['name'],
                contracts=[
                    sign_ocntract_model.Contract(
                        contract_id=contract['contract_id'],
                        versions=[
                            model.Version(
                                blob_id=model.BlobID(
                                    bid=version['blob_id'],
                                    timestamp=
                                    0,  # You can add timestamp if available in the DB
                                ),
                                initial_blob_data=model.BlobID(
                                    bid=version['initial_blob_data'],
                                    timestamp=0),
                                previous_versions=[
                                    model.BlobID(bid=prev_blob,
                                                 timestamp=0) for prev_blob in
                                    version['previous_versions']
                                ],
                                alias=version['alias'])
                            for version in contract['versions']
                        ]) for contract in client_data['contracts']
                ])
            return client

    # If client not found, raise an exception
    raise ValueError(f"Client with ID {client_id} not found.")


def GetContractsFromClient(
        client: sign_ocntract_model.Client
) -> list[sign_ocntract_model.Contract]:
    """
    Retrieves all contracts for a given client.
    """
    return client.contracts


def GetContracts(
        client_id: str, query_options: model.QueryOptions
) -> list[sign_ocntract_model.Contract]:
    """
    Retrieves contracts for a specific client, filtered by query options.
    """
    # Fetch the client by ID
    client = GetClientById(client_id)

    # Apply the query options (e.g., filter by time, version, etc.)
    filtered_contracts = []

    for contract in client.contracts:
        filtered_versions = []

        # Filter by time range, if provided
        if query_options.query_by_time:
            for version in contract.versions:
                if (query_options.query_by_time.after <=
                        version.blob_id.timestamp <=
                        query_options.query_by_time.before):
                    filtered_versions.append(version)
        else:
            filtered_versions = contract.versions  # No time filtering

        # Filter by version number, if provided
        if query_options.query_by_version is not None:
            filtered_versions = [
                v for v in filtered_versions
                if v.blob_id.version == query_options.query_by_version
            ]

        if filtered_versions:
            # Add the contract if any version matches the filters
            filtered_contracts.append(
                sign_ocntract_model.Contract(contract_id=contract.contract_id,
                                             versions=filtered_versions))

    return filtered_contracts


def AIPrompt() -> None:
    raise NotImplementedError('TODO')
