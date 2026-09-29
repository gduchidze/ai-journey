class VectorDBStore:
    def __init__(self):
        self.ids = []
        self.vectors = []

    def add(self, id, vector):
        self.ids.append(id)
        self.vectors.append(vector)

    def search(self, query_vector):
        pass