import json
from pathlib import Path
from app_paths import get_data_dir

DATA_DIR = get_data_dir()
DEFAULT_STATS_FILE = DATA_DIR / 'stats.json'


class StatsManager:
    """Manages loading, saving, and updating user statistics."""
    
    def __init__(self, stats_path=None):
        self.stats_path = Path(stats_path) if stats_path else DEFAULT_STATS_FILE
        self.stats = {}
        self._load_stats()

    def _load_stats(self):
        """Loads stats from the JSON file, or creates it if it doesn't exist."""
        if not self.stats_path.exists():
            self.stats_path.parent.mkdir(parents=True, exist_ok=True)
            self.stats = {}
            self.save_stats()
        else:
            with open(self.stats_path, 'r', encoding='utf-8') as f:
                try:
                    self.stats = json.load(f)
                except json.JSONDecodeError:
                    self.stats = {}

    def save_stats(self):
        """Saves the current stats to the JSON file."""
        self.stats_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.stats_path, 'w', encoding='utf-8') as f:
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
        self.save_stats()
