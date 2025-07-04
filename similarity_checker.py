from sentence_transformers import SentenceTransformer, util

class SimilarityChecker:
    """
    A class to check the semantic similarity between two texts using a pre-trained model.
    """
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        """
        Initializes the checker and loads the SentenceTransformer model.
        This may download the model files (approx. 471MB) on the first run.
        """
        print("Loading similarity model... This may take a moment on the first run.")
        self.model = SentenceTransformer(model_name)
        print("Similarity model loaded successfully.")

    def are_similar(self, text1, text2, threshold=0.6):
        """
        Calculates the semantic similarity between two texts and checks if it's above a threshold.

        Args:
            text1 (str): The first text.
            text2 (str): The second text.
            threshold (float): The similarity threshold (between 0 and 1).

        Returns:
            bool: True if the similarity is >= threshold, False otherwise.
        """
        if not text1 or not text2:
            return False

        # Encode the texts into embeddings
        embedding1 = self.model.encode(text1, convert_to_tensor=True)
        embedding2 = self.model.encode(text2, convert_to_tensor=True)

        # Compute cosine similarity
        cosine_scores = util.cos_sim(embedding1, embedding2)
        similarity = cosine_scores.item()

        print(f"Comparing '{text1}' and '{text2}'. Similarity score: {similarity:.4f}")

        return similarity >= threshold
