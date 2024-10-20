import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import model

class Contract(object):
    contract_id: str
    versions: list[model.Version]
    name: str

    def __init__(self, contract_id: str, versions: list[model.Version], name="default name"):
        self.contract_id = contract_id
        self.versions = versions 
        self.name = name

    def to_dict(self):
        return {
            "contract_id": self.contract_id,
            "versions": [version.to_dict() for version in self.versions],
            "name": self.name
        }


class Client(object):
    client_id: str
    name: str
    contracts: list[Contract]

    def __init__(self, client_id: str, name: str, contracts: list[Contract]):
        self.client_id = client_id
        self.name = name
        self.contracts = contracts

    def to_dict(self):
        return {
            "client_id": self.client_id,
            "name": self.name,
            "contracts": [contract.to_dict() for contract in self.contracts]
        }
