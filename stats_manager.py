import json
from pathlib import Path
from app_paths import get_data_dir

DATA_DIR = get_data_dir()
DEFAULT_STATS_FILE = DATA_DIR / 'stats.json'

# Mastery streak threshold: correct answers in a row to unlock next level
MASTERY_STREAK_THRESHOLD = 3

# Ordered list of study modes (progression order)
STUDY_MODES = [
    'translation_mc', 'translation_text',
    'definition_mc', 'definition_text',
    'synonym_mc', 'synonym_text'
]


class StatsManager:
    """Manages loading, saving, and updating user statistics with mastery tracking."""

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

    def _ensure_mode_stats(self, word_key):
        """Ensures per-mode stats exist for a word, migrating old format if needed."""
        if word_key not in self.stats:
            self.stats[word_key] = {'correct': 0, 'incorrect': 0}

        entry = self.stats[word_key]

        # Auto-migrate: add per-mode sub-dicts if missing
        for mode in STUDY_MODES:
            if mode not in entry:
                entry[mode] = {
                    'correct': 0, 'incorrect': 0,
                    'streak': 0, 'errors_in_row': 0
                }
            # Migrate existing entries that lack errors_in_row
            elif 'errors_in_row' not in entry[mode]:
                entry[mode]['errors_in_row'] = 0

    def record_answer(self, card, is_correct, mode='translation_mc'):
        """Records the result of an answer with mastery tracking.

        Soft downgrade logic on errors:
        - First error (streak > 0): reset streak to 0, level stays.
        - Second consecutive error (streak == 0): demote mastery level
          by resetting the previous level's streak to 0.
        """
        word_key = self._get_word_key(card)
        self._ensure_mode_stats(word_key)
        entry = self.stats[word_key]

        # Update global counters (backward compatibility)
        if is_correct:
            entry['correct'] = entry.get('correct', 0) + 1
        else:
            entry['incorrect'] = entry.get('incorrect', 0) + 1

        # Fallback for old mode names from older config/runs
        if mode not in STUDY_MODES:
            mode = f"{mode}_mc" if f"{mode}_mc" in STUDY_MODES else 'translation_mc'

        # Update per-mode counters
        mode_stats = entry[mode]
        if is_correct:
            mode_stats['correct'] += 1
            mode_stats['streak'] += 1
            mode_stats['errors_in_row'] = 0
        else:
            mode_stats['incorrect'] += 1
            mode_stats['errors_in_row'] = mode_stats.get('errors_in_row', 0) + 1

            if mode_stats['streak'] > 0:
                # First error: just reset streak, keep level
                print(f"[MASTERY] {word_key}: streak reset on {mode} "
                      f"(was {mode_stats['streak']})")
                mode_stats['streak'] = 0
            elif mode_stats['errors_in_row'] >= 2:
                # Two consecutive errors with streak=0: demote level
                mode_idx = STUDY_MODES.index(mode)
                if mode_idx > 0:
                    prev_mode = STUDY_MODES[mode_idx - 1]
                    entry[prev_mode]['streak'] = 0
                    print(f"[MASTERY] {word_key}: DEMOTED from {mode} "
                          f"to {prev_mode} (prev streak reset)")

    def get_mastery_level(self, card):
        """Returns the highest unlocked study mode for a card dynamically.

        Builds the active levels for this card and checks streaks.
        """
        word_key = self._get_word_key(card)
        self._ensure_mode_stats(word_key)
        entry = self.stats[word_key]

        has_uzbek = bool((card.get('uzbek') or '').strip())
        has_definition = bool((card.get('definition') or '').strip())
        has_synonyms = bool(card.get('synonyms'))

        levels = []
        if has_uzbek:
            levels.extend(['translation_mc', 'translation_text'])
        if has_definition:
            levels.extend(['definition_mc', 'definition_text'])
        if has_synonyms:
            levels.extend(['synonym_mc', 'synonym_text'])

        if not levels:
            levels.append('translation_mc')

        current_level = levels[0]
        for lvl in levels[:-1]:
            if entry[lvl]['streak'] >= MASTERY_STREAK_THRESHOLD:
                next_idx = levels.index(lvl) + 1
                current_level = levels[next_idx]
            else:
                break
        return current_level

    def get_streak(self, card, mode='translation'):
        """Returns the current streak for a specific mode."""
        word_key = self._get_word_key(card)
        self._ensure_mode_stats(word_key)
        return self.stats[word_key][mode]['streak']

    def get_stats_for_word(self, card):
        """Retrieves the stats for a specific card (backward compatible)."""
        word_key = self._get_word_key(card)
        self._ensure_mode_stats(word_key)
        return self.stats.get(word_key, {'correct': 0, 'incorrect': 0})

    def get_all_stats(self):
        """Returns all statistics."""
        return self.stats

    def reset_stats(self):
        """Resets all statistics and saves the empty state."""
        self.stats = {}
        self.save_stats()
