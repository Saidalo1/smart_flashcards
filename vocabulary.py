import json
import random
import uuid
from pathlib import Path
from app_paths import get_data_dir

DATA_PATH = get_data_dir() / "vocabulary.json"
# --- Adaptive Session Deck Constants ---
# The ideal session size will be total_words / SESSION_SIZE_DIVISOR
SESSION_SIZE_DIVISOR = 3
# But it will be clamped between these two values
MIN_SESSION_SIZE = 20
MAX_SESSION_SIZE = 40
# ------------------------------------

class Vocabulary:
    """Manages loading and providing vocabulary words from a shuffled deck."""

    def __init__(self, data_path=DATA_PATH):
        """Initializes the vocabulary and loads words."""
        self.words = []
        self.deck = []
        self.data_path = data_path
        self._stats_manager = None
        self._active_topics = None
        self.load_words()
        self.migrate_vocabulary()
        # Note: shuffle_deck() should be called from main.py with stats_manager

    def load_words(self):
        """Loads words from the JSON file."""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.words = json.load(f)
            print(f"Loaded {len(self.words)} words from vocabulary.")
        except (FileNotFoundError, json.JSONDecodeError):
            self.words = []
            print("Vocabulary file not found or corrupted. Starting with an empty list.")

    def shuffle_deck(self, stats_manager=None, active_topics=None):
        """Creates a shuffled deck using weighted selection, filtered by topic."""
        # Remember settings for auto-reshuffle
        if stats_manager is not None:
            self._stats_manager = stats_manager
        if active_topics is not None:
            self._active_topics = active_topics
        
        print(f"[SHUFFLE] === SHUFFLE_DECK CALLED ===")
        print(f"[SHUFFLE] Active topics: {self._active_topics}")
        print(f"[SHUFFLE] Total words in vocabulary: {len(self.words)}")
        
        # Filter by active topics
        if self._active_topics:
            filtered_words = [w for w in self.words if w.get('category') in self._active_topics]
            print(f"[SHUFFLE] Words matching active topics: {len(filtered_words)}")
            for w in filtered_words[:5]:
                print(f"[SHUFFLE]   - {w['english']} (category: {w.get('category')})")
            if len(filtered_words) > 5:
                print(f"[SHUFFLE]   ... and {len(filtered_words) - 5} more")
        else:
            filtered_words = self.words
            print(f"[SHUFFLE] No topic filter - using all words")
        
        if not filtered_words:
            self.deck = []
            print("[SHUFFLE] No words match active topics. Deck is empty.")
            return

        print(f"Creating smart session deck from {len(filtered_words)} words...")
        total_words = len(filtered_words)

        # --- Smart Session Sizing ---
        desired_size = total_words // SESSION_SIZE_DIVISOR
        clamped_size = max(MIN_SESSION_SIZE, min(MAX_SESSION_SIZE, desired_size))
        session_size = min(clamped_size, total_words)

        # --- Weighted Selection Based on Stats ---
        if self._stats_manager:
            weights = []
            for word in filtered_words:
                stats = self._stats_manager.get_stats_for_word(word)
                correct = stats.get('correct', 0)
                incorrect = stats.get('incorrect', 0)
                total = correct + incorrect

                if total == 0:
                    weight = 1.5  # Never shown
                else:
                    error_rate = incorrect / total
                    weight = 0.5 + (error_rate * 2.0)
                
                weights.append(weight)

            self.deck = random.choices(filtered_words, weights=weights, k=session_size)
            # Remove duplicates
            seen = set()
            unique_deck = []
            for card in self.deck:
                if card['id'] not in seen:
                    seen.add(card['id'])
                    unique_deck.append(card)
            self.deck = unique_deck[:session_size]
        else:
            self.deck = random.sample(filtered_words, session_size)

        print(f"[SHUFFLE] Created session deck with {len(self.deck)} cards:")
        for card in self.deck:
            print(f"[SHUFFLE]   - {card['english']} (category: {card.get('category')})")

    def get_all_topics(self):
        """Returns a list of all unique topic/category names, sorted numerically."""
        import re
        topics = set()
        for word in self.words:
            if 'category' in word and word['category']:
                topics.add(word['category'])

        def sort_key(topic):
            """Extracts the first number from category name for numerical sorting."""
            match = re.search(r'\((\d+)', topic)
            return int(match.group(1)) if match else 0

        return sorted(list(topics), key=sort_key)

    def get_grouped_topics(self):
        """Returns topics grouped by prefix, e.g. {'SAT Vocabulary': ['SAT Vocabulary (1-15)', ...]}."""
        import re
        from collections import OrderedDict

        all_topics = self.get_all_topics()
        groups = OrderedDict()

        for topic in all_topics:
            # Split "SAT Vocabulary (1-15)" → group="SAT Vocabulary", sub="1-15"
            match = re.match(r'^(.+?)\s*\((.+)\)$', topic)
            if match:
                group_name = match.group(1).strip()
            else:
                group_name = topic

            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(topic)

        return groups

    def get_word_count_for_topic(self, topic):
        """Returns the number of words in a specific topic/category."""
        return len([w for w in self.words if w.get('category') == topic])

    def save_words(self):
        """Saves the current list of words back to the JSON file."""
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.words, f, indent=2, ensure_ascii=False)
            print(f"Vocabulary saved with {len(self.words)} words.")
        except IOError as e:
            print(f"Error saving vocabulary: {e}")

    def delete_word(self, english_word_to_delete):
        """Removes a word from the vocabulary by its English name and saves the changes."""
        card_to_delete = None
        for word in self.words:
            if word['english'] == english_word_to_delete:
                card_to_delete = word
                break

        if card_to_delete:
            self.words.remove(card_to_delete)
            # Also remove from the current deck if it's there
            self.deck = [card for card in self.deck if card.get('id') != card_to_delete.get('id')]
            self.save_words()
            print(f"Deleted '{english_word_to_delete}' from vocabulary.")
            return True
        else:
            print(f"Could not find '{english_word_to_delete}' to delete.")
            return False

    def delete_topic(self, category):
        """Removes every word in a category (topic) and saves. Returns how many
        words were removed."""
        before = len(self.words)
        self.words = [w for w in self.words if w.get('category') != category]
        self.deck = [c for c in self.deck if c.get('category') != category]
        removed = before - len(self.words)
        if removed:
            self.save_words()
            print(f"Deleted topic '{category}' ({removed} words).")
        return removed

    def get_all_words(self):
        """Returns the entire list of word pairs."""
        return self.words

    def add_word(self, english, uzbek):
        """Adds a new word to the vocabulary if it doesn't already exist."""
        # Case-insensitive check for existence
        if any(w['english'].lower() == english.lower() for w in self.words):
            return False  # Word already exists

        new_word = {
            "english": english,
            "uzbek": uzbek,
            "id": str(uuid.uuid4()),
            "last_shown": None,
            "correct_answers": 0,
            "total_answers": 0,
            "complexity": 0.5  # Default complexity
        }
        self.words.append(new_word)
        self.save_words()
        print(f"Added word: {english}")
        return True

    def add_words_to_topic(self, category, pairs, default_complexity=0.5):
        """Adds several words under one topic/category at once.

        `pairs` is an iterable of dicts with at least 'english' (and usually
        'uzbek'). Optional per-row keys: 'hint', 'definition', 'grammar_pattern',
        'synonyms' (a list, or a comma-separated string). Duplicate English words
        (case-insensitive) are skipped. Saves once. Returns how many were added.
        """
        category = (category or '').strip()
        existing = {w['english'].lower() for w in self.words}
        added = 0
        for row in pairs:
            english = (row.get('english') or '').strip()
            uzbek = (row.get('uzbek') or '').strip()
            if not english or english.lower() in existing:
                continue
            hint = (row.get('hint') or '').strip() or None
            definition = (row.get('definition') or '').strip() or None
            grammar_pattern = (row.get('grammar_pattern') or '').strip() or None
            synonyms = row.get('synonyms') or []
            if isinstance(synonyms, str):
                synonyms = [s.strip() for s in synonyms.split(',') if s.strip()]
            self.words.append({
                "english": english,
                "uzbek": uzbek,
                "category": category,
                "grammar_pattern": grammar_pattern,
                "id": str(uuid.uuid4()),
                "last_shown": None,
                "correct_answers": 0,
                "total_answers": 0,
                "complexity": default_complexity,
                "definition": definition,
                "synonyms": synonyms,
                "hint": hint,
            })
            existing.add(english.lower())
            added += 1
        if added:
            self.save_words()
        print(f"Added {added} word(s) to topic '{category}'.")
        return added

    def update_word(self, old_english, new_english, new_uzbek):
        """Updates an existing word."""
        for word in self.words:
            if word['english'].lower() == old_english.lower():
                word['english'] = new_english
                word['uzbek'] = new_uzbek
                self.save_words()
                print(f"Updated word: {old_english} -> {new_english}")
                return True
        return False

    def migrate_vocabulary(self):
        """Checks for old format words and adds new fields if necessary."""
        needs_saving = False
        for word in self.words:
            if 'id' not in word:
                needs_saving = True
                word['id'] = str(uuid.uuid4())
                word['last_shown'] = None
                word['correct_answers'] = 0
                word['total_answers'] = 0
                word['complexity'] = 0.5  # Default complexity

            # Migrate: add definition and synonyms fields if missing
            if 'definition' not in word:
                needs_saving = True
                word['definition'] = None
            if 'synonyms' not in word:
                needs_saving = True
                word['synonyms'] = []

        if needs_saving:
            print("Migrating vocabulary format (adding new fields)...")
            self.save_words()
            print("Migration complete.")

    def get_random_card(self):
        """Gets the next card from the deck. Reshuffles if the deck is empty."""
        if not self.deck:
            if not self.words:
                return None
            print("Deck is empty. Reshuffling...")
            self.shuffle_deck()

        card = self.deck.pop(0)
        print(f"[CARD] === SHOWING CARD ===")
        print(f"[CARD] Word: {card['english']} -> {card.get('uzbek', 'N/A')}")
        print(f"[CARD] Category: {card.get('category')}")
        return card

    def get_options_for_card(self, correct_card, language='uzbek'):
        """Generates multiple choice options for a given card (from same category only)."""
        # Filter words by the same category as the correct card
        card_category = correct_card.get('category')
        print(f"[OPTIONS] Generating options for: {correct_card['english']}")
        print(f"[OPTIONS] Card category: {card_category}")
        
        if card_category:
            same_category_words = [w for w in self.words if w.get('category') == card_category]
            print(f"[OPTIONS] Words in same category: {len(same_category_words)}")
        else:
            same_category_words = self.words
            print(f"[OPTIONS] No category - using all {len(same_category_words)} words")
        
        if len(same_category_words) < 4:
            # Widen the distractor pool to all words. If there still aren't 4,
            # show whatever options exist (even a single one) rather than nothing.
            print(f"[OPTIONS] Few words in category — widening to all words.")
            same_category_words = self.words
        if not same_category_words:
            return []

        correct_answer = correct_card[language]
        options = {correct_answer}

        # Get distractors only from the same category
        attempts = 0
        while len(options) < 4 and attempts < 50:
            attempts += 1
            random_word = random.choice(same_category_words)
            if random_word[language] not in options:
                options.add(random_word[language])

        shuffled_options = list(options)
        random.shuffle(shuffled_options)
        print(f"[OPTIONS] Generated options: {shuffled_options}")
        return shuffled_options
