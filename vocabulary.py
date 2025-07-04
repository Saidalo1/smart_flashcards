import json
import random
import uuid
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "vocabulary.json"
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
        """Initializes the vocabulary, loads words, and creates the first deck."""
        self.words = []
        self.deck = []
        self.data_path = data_path
        self.load_words()
        self.migrate_vocabulary() # Ensure all words have the new format
        self.shuffle_deck()  # Create the initial deck

    def load_words(self):
        """Loads words from the JSON file."""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.words = json.load(f)
            print(f"Loaded {len(self.words)} words from vocabulary.")
        except (FileNotFoundError, json.JSONDecodeError):
            self.words = []
            print("Vocabulary file not found or corrupted. Starting with an empty list.")

    def shuffle_deck(self):
        """Creates a new shuffled deck for a study session using an adaptive size."""
        if not self.words:
            self.deck = []
            print("Vocabulary is empty. No deck created.")
            return

        print("Shuffling a new session deck...")
        total_words = len(self.words)

        # --- Smart Session Sizing Formula ---
        # 1. Calculate a proportional size (e.g., one-third of the vocabulary).
        desired_size = total_words // SESSION_SIZE_DIVISOR
        # 2. Clamp it between a practical minimum and maximum.
        clamped_size = max(MIN_SESSION_SIZE, min(MAX_SESSION_SIZE, desired_size))
        # 3. Ensure the deck isn't larger than the available words (for small vocabularies).
        session_size = min(clamped_size, total_words)
        # ---

        # Create the session deck by sampling from the main word list
        self.deck = random.sample(self.words, session_size)

        print(f"Created a new session deck with {len(self.deck)} random cards (out of {total_words} total).")

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
                word['complexity'] = 0.5 # Default complexity
        
        if needs_saving:
            print("Migrating old vocabulary format to new format...")
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
        return card

    def get_options_for_card(self, correct_card, language='uzbek'):
        """Generates multiple choice options for a given card."""
        if len(self.words) < 4:
            return []  # Not enough words to generate options

        correct_answer = correct_card[language]
        options = {correct_answer}

        # To get distractors, we can just pick random words from the full list
        while len(options) < 4:
            # Make sure we don't get stuck in an infinite loop if all words have same translation
            if len(options) >= len(self.words):
                break
            random_word = random.choice(self.words)
            # Ensure we don't add the same option text if different words have the same translation
            if random_word[language] not in options:
                options.add(random_word[language])

        shuffled_options = list(options)
        random.shuffle(shuffled_options)
        return shuffled_options
