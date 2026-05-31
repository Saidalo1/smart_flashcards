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
        Handles hierarchical structures (with '->') by evaluating components independently.
        """
        if not text1 or not text2:
            return False

        text1_clean = text1.strip()
        text2_clean = text2.strip()

        # 1. Если оба текста содержат структуру категорий '->'
        if "->" in text1_clean and "->" in text2_clean:
            parts1 = [p.strip().lower() for p in text1_clean.split("->")]
            parts2 = [p.strip().lower() for p in text2_clean.split("->")]

            # Если в структуре разное количество уровней, они сразу не равны
            if len(parts1) != len(parts2):
                print(f"Structure mismatch: '{text1_clean}' vs '{text2_clean}'")
                return False

            # Покомпонентная проверка, чтобы убрать префиксный шум
            for p1, p2 in zip(parts1, parts2):
                if p1 == p2:
                    continue  # Компоненты идентичны, проверяем следующий уровень

                # Если компоненты разные, проверяем их изолированную семантику
                emb1 = self.model.encode(p1, convert_to_tensor=True)
                emb2 = self.model.encode(p2, convert_to_tensor=True)
                component_similarity = util.cos_sim(emb1, emb2).item()

                # Если хоть один уровень иерархии не прошел порог — ответ неверный
                if component_similarity < threshold:
                    print(f"Component mismatch ('{p1}' vs '{p2}'). Score: {component_similarity:.4f}")
                    return False

            print(f"Hierarchical match successful for: '{text1_clean}' and '{text2_clean}'")
            return True

        # 2. Фолбек (стандартное поведение) для обычных примеров без '->'
        embedding1 = self.model.encode(text1_clean, convert_to_tensor=True)
        embedding2 = self.model.encode(text2_clean, convert_to_tensor=True)

        cosine_scores = util.cos_sim(embedding1, embedding2)
        similarity = cosine_scores.item()

        print(f"Comparing '{text1_clean}' and '{text2_clean}'. Similarity score: {similarity:.4f}")

        return similarity >= threshold