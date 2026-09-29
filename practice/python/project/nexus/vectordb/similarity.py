import numpy as np

# cosine similarity is a measure of similarity between two non-zero vectors of an inner product space that measures the cosine of the angle between them. It is the dot product of the vectors divided by the product of their magnitudes.
def cosine_similarity(query_vector, vectors):
    return [np.dot(query_vector, vector) / (np.linalg.norm(query_vector) * np.linalg.norm(vector)) for vector in vectors]

def euclidean_similarity(query_vector, vectors):
    return [np.linalg.norm(query_vector - vector) for vector in vectors]

def manhattan_similarity(query_vector, vectors):
    return [np.linalg.norm(query_vector - vector, ord=1) for vector in vectors]

def jaccard_similarity(query_vector, vectors):
    return [np.linalg.norm(query_vector - vector, ord=1) for vector in vectors]