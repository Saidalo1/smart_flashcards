import os
from sentence_transformers import SentenceTransformer, util
from app_paths import get_data_dir


MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'


class SimilarityChecker:
    """
    A class to check the semantic similarity between two texts using a pre-trained model.
    """
    def __init__(self, model_name=MODEL_NAME):
        """
        Initializes the checker and loads the SentenceTransformer model.
        Model is saved locally in data/models/similarity_model/ for persistence.
        """
        local_model_dir = get_data_dir() / 'models' / 'similarity_model'

        if local_model_dir.exists() and any(local_model_dir.iterdir()):
            # Load from local saved copy (no HuggingFace cache involved)
            print(f"Loading similarity model from local: {local_model_dir}")
            self.model = SentenceTransformer(str(local_model_dir))
        else:
            # First run: download model, then save locally
            print(f"Downloading similarity model '{model_name}' (first run only)...")
            # Use default HuggingFace cache for download
            os.environ.setdefault('HF_HOME', str(get_data_dir() / 'hf_cache'))
            self.model = SentenceTransformer(model_name)
            # Save to clean local folder (no cache structure)
            local_model_dir.mkdir(parents=True, exist_ok=True)
            self.model.save(str(local_model_dir))
            print(f"Model saved to: {local_model_dir}")

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
