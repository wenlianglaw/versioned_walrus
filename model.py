class BlobID(object):
    bid: str
    timestamp: int
    def __init__(self, bid, timestamp):
      self.bid = bid
      self.timestamp = timestamp

    def to_dict(self):
        return {
            "bid": self.bid,
            "timestamp": self.timestamp
        }

class Version(object):
    # This data's blob ID
    blob_id: BlobID

    # The original version's blob ID
    initial_blob_data: BlobID

    # All the previous versions
    previous_versions: list[BlobID]

    # Alias
    alias: str

    def __init__(self,
                 blob_id: BlobID,
                 initial_blob_data: BlobID = None,
                 previous_versions: list[BlobID] = None,
                 alias: str = None):
        self.blob_id = blob_id
        self.initial_blob_data = initial_blob_data
        self.previous_versions = previous_versions
        self.alias = alias

    def add_version(self, blob_id):
        self.previous_versions.append(blob_id)

    def to_dict(self):
        return {
            "blob_id": self.blob_id.bid,
            "initial_blob_data": self.initial_blob_data.bid,
            "previous_versions": [v.bid for v in self.previous_versions],
            "alias": self.alias
        }

class QueryOptions(object):
    query_by_version: int

    # Use AI to filter the the results.
    query_description: str

    def __init__(self):
        pass
