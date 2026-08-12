import os

MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'

# RapidFuzz gives a fast, dependency-light string-similarity pass that forgives
# typos/case/spacing. It's optional: if missing we simply skip the fast pass.
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    fuzz = None
    RAPIDFUZZ_AVAILABLE = False


class SimilarityChecker:
    """Grades a typed answer against the expected one.

    Hybrid strategy:
      1. RapidFuzz string match — forgives typos/case/spacing (strict, instant).
      2. Semantic model fallback — accepts synonyms/paraphrases, only if loaded.

    The semantic model (sentence-transformers + torch) is heavy, so it is imported
    lazily and only when `use_semantic` is True. A strict, lightweight build can set
    `use_semantic=False` to skip the model entirely (no torch, no ~470 MB download)
    and rely on RapidFuzz alone.
    """

    def __init__(self, model_name=MODEL_NAME, threshold=0.6, fuzz_threshold=85,
                 use_semantic=True):
        self.threshold = threshold
        self.fuzz_threshold = fuzz_threshold
        self.model = None
        self._util = None

        if not RAPIDFUZZ_AVAILABLE:
            print("Warning: rapidfuzz not installed — fast string grading disabled.")

        if not use_semantic:
            print("Semantic grading disabled — using RapidFuzz only (no model download).")
            return

        try:
            from app_paths import get_cache_dir
            from sentence_transformers import SentenceTransformer, util
            self._util = util

            local_model_dir = get_cache_dir() / 'models' / 'similarity_model'
            if local_model_dir.exists() and any(local_model_dir.iterdir()):
                print(f"Loading similarity model from local: {local_model_dir}")
                self.model = SentenceTransformer(str(local_model_dir))
            else:
                print(f"Downloading similarity model '{model_name}' (first run only)...")
                os.environ.setdefault('HF_HOME', str(get_cache_dir() / 'hf_cache'))
                self.model = SentenceTransformer(model_name)
                local_model_dir.mkdir(parents=True, exist_ok=True)
                self.model.save(str(local_model_dir))
                print(f"Model saved to: {local_model_dir}")
            print("Similarity model loaded successfully.")
        except Exception as e:
            self.model = None
            print(f"Could not load similarity model ({e}). "
                  f"Falling back to RapidFuzz string matching only.")

    def _fuzzy_match(self, a, b):
        """Fast, typo-tolerant string match. True if strings are close enough."""
        if not RAPIDFUZZ_AVAILABLE:
            return False
        a1, b1 = a.lower(), b.lower()
        if a1 == b1:
            return True
        score = max(fuzz.ratio(a1, b1), fuzz.token_sort_ratio(a1, b1))
        if score >= self.fuzz_threshold:
            print(f"Fuzzy match: '{a}' ~ '{b}' (score {score:.0f} >= {self.fuzz_threshold})")
            return True
        return False

    def are_similar(self, text1, text2, threshold=None):
        """
        Returns True if `text1` is an acceptable answer for `text2`.

        Tries a strict RapidFuzz string match first (typos), then, only if the
        semantic model is loaded, a meaning-based check. Hierarchical answers
        (with '->') are compared component-by-component semantically.

        When `threshold` is None, the instance default (self.threshold) is used.
        """
        if threshold is None:
            threshold = self.threshold
        if not text1 or not text2:
            return False

        text1_clean = text1.strip()
        text2_clean = text2.strip()

        has_arrow = "->" in text1_clean and "->" in text2_clean

        # 1. Fast string pass (skip for hierarchical '->' answers).
        if not has_arrow and self._fuzzy_match(text1_clean, text2_clean):
            return True

        # 2. Semantic fallback — only if the model is available.
        if self.model is None:
            return False
        util = self._util

        # 2a. Hierarchical structures ('->'): evaluate each level independently.
        if has_arrow:
            parts1 = [p.strip().lower() for p in text1_clean.split("->")]
            parts2 = [p.strip().lower() for p in text2_clean.split("->")]
            if len(parts1) != len(parts2):
                print(f"Structure mismatch: '{text1_clean}' vs '{text2_clean}'")
                return False
            for p1, p2 in zip(parts1, parts2):
                if p1 == p2:
                    continue
                emb1 = self.model.encode(p1, convert_to_tensor=True)
                emb2 = self.model.encode(p2, convert_to_tensor=True)
                component_similarity = util.cos_sim(emb1, emb2).item()
                if component_similarity < threshold:
                    print(f"Component mismatch ('{p1}' vs '{p2}'). Score: {component_similarity:.4f}")
                    return False
            print(f"Hierarchical match successful for: '{text1_clean}' and '{text2_clean}'")
            return True

        # 2b. Plain semantic comparison.
        embedding1 = self.model.encode(text1_clean, convert_to_tensor=True)
        embedding2 = self.model.encode(text2_clean, convert_to_tensor=True)
        similarity = util.cos_sim(embedding1, embedding2).item()
        print(f"Comparing '{text1_clean}' and '{text2_clean}'. Similarity score: {similarity:.4f}")
        return similarity >= threshold
