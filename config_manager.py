"""
Configuration manager for Smart Flashcards.
Persists user settings to a JSON file.
"""
import json
from pathlib import Path
from app_paths import get_data_dir

DATA_DIR = get_data_dir()
DEFAULT_CONFIG_FILE = DATA_DIR / 'config.json'

# Default settings
DEFAULT_CONFIG = {
    'timer_interval': 30,
    'hotkey': 'F7',
    'card_position': 'bottom_right',  # bottom_right, mouse, center, top_right, top_left, bottom_left
    'active_topics': [],
    'topic_weights': {},
    'show_notifications': True,
    'theme': 'dark',
    'study_mode': 'adaptive',
    # How close a typed answer must be to count as correct (0..1). Higher = stricter.
    # You (watching the logs) can keep it low; a build for friends should be stricter
    # so a wrong-but-related word isn't accepted.
    'similarity_threshold': 0.6,
    # String-similarity accept cutoff (0..100) for the fast RapidFuzz pass that
    # forgives typos/case/spacing before any semantic check.
    'fuzz_threshold': 85,
    # Whether to use the semantic model as a fallback (accepts synonyms/paraphrases).
    # Turn OFF for a strict, lightweight build (RapidFuzz only, no model download).
    'semantic_grading': True,
}


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path=None):
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_FILE
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """Loads config from JSON file, creates with defaults if missing."""
        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config = DEFAULT_CONFIG.copy()
            self.save_config()
        else:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in DEFAULT_CONFIG.items():
                    if key not in self.config:
                        self.config[key] = value
            except json.JSONDecodeError:
                self.config = DEFAULT_CONFIG.copy()
                self.save_config()
    
    def save_config(self):
        """Saves current config to JSON file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get(self, key, default=None):
        """Gets a config value."""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Sets a config value and saves."""
        self.config[key] = value
        self.save_config()
    
    @property
    def timer_interval(self):
        """Timer interval in seconds."""
        return self.config.get('timer_interval', 30)
    
    @timer_interval.setter
    def timer_interval(self, value):
        self.config['timer_interval'] = value
        self.save_config()
    
    @property
    def hotkey(self):
        """Hotkey for showing next card."""
        return self.config.get('hotkey', 'F7')
    
    @hotkey.setter
    def hotkey(self, value):
        self.config['hotkey'] = value
        self.save_config()
    
    @property
    def active_topics(self):
        """List of active topic names. Empty = all active."""
        return self.config.get('active_topics', [])
    
    @active_topics.setter
    def active_topics(self, value):
        self.config['active_topics'] = value
        self.save_config()

    @property
    def card_position(self):
        """Position for flashcard widget."""
        return self.config.get('card_position', 'bottom_right')
    
    @card_position.setter
    def card_position(self, value):
        self.config['card_position'] = value
        self.save_config()

    @property
    def similarity_threshold(self):
        """Semantic-similarity accept threshold (0..1). Higher = stricter grading."""
        return self.config.get('similarity_threshold', 0.6)

    @similarity_threshold.setter
    def similarity_threshold(self, value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = 0.6
        value = max(0.0, min(1.0, value))
        self.config['similarity_threshold'] = value
        self.save_config()

    @property
    def fuzz_threshold(self):
        """RapidFuzz string-similarity accept cutoff (0..100). Higher = stricter."""
        return self.config.get('fuzz_threshold', 85)

    @fuzz_threshold.setter
    def fuzz_threshold(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = 85
        self.config['fuzz_threshold'] = max(0, min(100, value))
        self.save_config()

    @property
    def semantic_grading(self):
        """Whether to load the semantic model for synonym-aware grading."""
        return bool(self.config.get('semantic_grading', True))

    @semantic_grading.setter
    def semantic_grading(self, value):
        self.config['semantic_grading'] = bool(value)
        self.save_config()

    @property
    def study_mode(self):
        """Study mode: 'adaptive', 'translation', 'definition', or 'synonym'."""
        return self.config.get('study_mode', 'adaptive')

    @study_mode.setter
    def study_mode(self, value):
        valid_modes = ('adaptive', 'translation', 'definition', 'synonym')
        if value not in valid_modes:
            print(f"Invalid study mode '{value}', defaulting to 'adaptive'")
            value = 'adaptive'
        self.config['study_mode'] = value
        self.save_config()

