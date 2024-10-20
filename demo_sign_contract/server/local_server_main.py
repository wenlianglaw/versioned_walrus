# This file is a local server that takes the frontend requests.
#
# For simplificy, we use json as the local DB.
#
# The local DB stores the user data, the contracts metadata and other sensitive
# data.
#
# The walrus DB store the encrypted signed contract and signature info.

import os
import sys

from http.server import BaseHTTPRequestHandler, HTTPServer
from requests_toolbelt.multipart import decoder

sys.path.insert(1, os.path.join(sys.path[0], '..'))
sys.path.insert(1, os.path.join(sys.path[0], '../..'))
import json
import local_db
import versioned_walrus
import model

# Local server port.
PORT = 8887


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Handle GET requests
        path = self.path

        if path == '/get_clients':
            self.get_clients()
        else:
            self.send_error(404, 'Endpoint not supported.')

    def do_POST(self):
        if self.path == '/sign_contract':
            self.sign_contract()
        if self.path == '/upload_contract':
            self.upload_contract()
        else:
            self.send_error(404, 'Method not supported.')

    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    # Ideally, we should use Sign service.
    # TODO: Go to the help desk.  Their user doc's examples links are invalid.
    def sign_contract(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        print(post_data)

        # Extract relevant data from request
        client_id = data['client_id']
        contract_id = data['contract_id']
        version_blob_id = data['version_blob_id']

        # Load the database
        db = local_db.LoadDatabase()

        print("DB: ", db)

        # Find the contract and version in the database
        client = next(
            (client
             for client in db['clients'] if client['client_id'] == client_id),
            None)
        if not client:
            self.send_error(404, 'Client not found.')
            return

        contract = next((contract for contract in client['contracts']
                         if contract['contract_id'] == contract_id), None)
        if not contract:
            self.send_error(404, 'Contract not found.')
            return

        version = next(
            (s
             for s in contract['versions'] if s['blob_id'] == version_blob_id),
            None)
        if not version:
            self.send_error(404, 'Contract version not found.')
            return

        # Save the updated database
        local_db.SaveDatabase(db)
        # Simple response with a success message
        response = {
            'status': 'success',
            'message': '[Addr] has signed [BlobID].'
        }

        print("\n\n", json.dumps(response).encode('utf-8'), "\n\n")

        # Send the JSON response
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def get_clients(self):
        # Add CORS headers
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        # Load the database
        db = local_db.LoadDatabase()

        clients_data = []
        for client in db['clients']:
            contracts = []
            for contract in client['contracts']:
                contract_versions = [{
                    'alias': s['alias'],
                    'blob_id': s['blob_id']
                } for s in contract['versions']]
                contracts.append({
                    'contract_id': contract['contract_id'],
                    'versions': contract_versions
                })
            clients_data.append({
                'client_id': client['client_id'],
                'name': client['name'],
                'contracts': contracts
            })

        # Send the client data as response
        self.wfile.write(json.dumps(clients_data).encode('utf-8'))

    # TODO
    # Placeholder for file upload implementation
    def upload_contract(self):
        # Read the content-length to get the size of the incoming data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)  # Read the raw POST data

        # Get the content-type and boundary from headers
        content_type = self.headers['Content-Type']

        # Parse the multipart form data
        multipart_data = decoder.MultipartDecoder(post_data, content_type)

        client_id = None
        contract_id = None
        version_alias = None
        file_data = None
        file_name = None
        # Also used as version id
        blob_id = None

        # Loop over the parts of the multipart data
        for part in multipart_data.parts:
            content_disposition = part.headers.get(
                b'Content-Disposition').decode('utf-8')

            print(content_disposition, ': ', part.text)

            # Parse form fields
            if 'name="client_id"' in content_disposition:
                client_id = part.text
            elif 'name="contract_id"' in content_disposition:
                contract_id = part.text
            elif 'name="version_alias"' in content_disposition:
                version_alias = part.text
            elif 'name="file"' in content_disposition:
                file_data = part.content  # This is the file content
                file_name = part.headers.get(b'Content-Disposition').decode(
                    'utf-8').split('filename=')[1].strip('"')
            elif 'blob_id' in content_disposition:
                blob_id = part.text

        # Validate the form data
        if client_id and contract_id and version_alias and file_data and file_name:
            # Save the file to the current working directory
            directory = os.path.join(os.getcwd(), 'tmp')
            file_path = os.path.join(directory, file_name)
            if not os.path.exists(directory):
                os.makedirs(directory)

            with open(file_path, 'wb') as output_file:
                output_file.write(file_data)

            # Send a JSON response back
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # Upload a new version
            updated_version: model.Version = versioned_walrus.UploadFileOnVersion(
                file_path, client_id, blob_id)

            print(updated_version)

            response = {
                'status':
                'success',
                'message':
                f'File {file_name} uploaded successfully for client ' +
                f'{client_id}.  New version ID: {updated_version.blob_id.bid}'
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            # Missing required form data
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                'status': 'fail',
                'message': 'Invalid or incomplete form data.'
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))


def run(server_class=HTTPServer, handler_class=RequestHandler, port=PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Server running on port {port}...')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
