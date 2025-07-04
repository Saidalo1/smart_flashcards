import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'
STATS_FILE = DATA_DIR / 'stats.json'

class StatsManager:
    """Manages loading, saving, and updating user statistics."""
    def __init__(self):
        self.stats = {}
        self._load_stats()

    def _load_stats(self):
        """Loads stats from the JSON file, or creates it if it doesn't exist."""
        if not STATS_FILE.exists():
            DATA_DIR.mkdir(exist_ok=True)
            self.stats = {}
            self.save_stats()
        else:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                try:
                    self.stats = json.load(f)
                except json.JSONDecodeError:
                    # Handle cases where the file is empty or corrupted
                    self.stats = {}

    def save_stats(self):
        """Saves the current stats to the JSON file."""
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=4, ensure_ascii=False)

    def _get_word_key(self, card):
        """Generates a consistent key for a word card (using English word)."""
        return card['english'].lower()

    def record_answer(self, card, is_correct):
        """Records the result of an answer for a given card."""
        word_key = self._get_word_key(card)
        if word_key not in self.stats:
            self.stats[word_key] = {'correct': 0, 'incorrect': 0}

        if is_correct:
            self.stats[word_key]['correct'] += 1
        else:
            self.stats[word_key]['incorrect'] += 1

    def get_stats_for_word(self, card):
        """Retrieves the stats for a specific card."""
        word_key = self._get_word_key(card)
        return self.stats.get(word_key, {'correct': 0, 'incorrect': 0})
        
    def get_all_stats(self):
        """Returns all statistics."""
        return self.stats

    def reset_stats(self):
        """Resets all statistics and saves the empty state."""
        self.stats = {}
        self._save_stats()
