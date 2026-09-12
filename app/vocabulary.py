import json
import random
import uuid
from pathlib import Path
from .app_paths import get_data_dir

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

    def shuffle_deck(self, stats_manager=None, active_topics=None, hardest_first=None):
        """Creates a shuffled deck, filtered by topic.

        Two selection modes:
          * default — weighted-random, favouring words answered wrong / never shown.
          * hardest_first=True — deterministic: worst-remembered (and new) words first.

        The deck is de-duplicated by English word, so a word that lives in several
        selected topics is studied ONCE per session (its answers are still accepted
        from any of those topics during grading).
        """
        # Remember settings for auto-reshuffle
        if stats_manager is not None:
            self._stats_manager = stats_manager
        if active_topics is not None:
            self._active_topics = active_topics
        if hardest_first is not None:
            self._hardest_first = hardest_first
        hardest_first = getattr(self, '_hardest_first', False)

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

        def dedup_by_english(cards):
            """One card per English word — a word shared by several selected topics
            is studied once (grading still accepts every topic's translation)."""
            seen, out = set(), []
            for c in cards:
                en = (c.get('english') or '').strip().lower()
                if en and en in seen:
                    continue
                seen.add(en)
                out.append(c)
            return out

        if hardest_first and self._stats_manager:
            # Worst-remembered (lowest accuracy) and never-shown come first.
            def accuracy(word):
                st = self._stats_manager.get_stats_for_word(word)
                c = st.get('correct', 0); i = st.get('incorrect', 0); t = c + i
                return (c / t) if t > 0 else 0.0   # new & all-wrong sort to the top
            ordered = sorted(filtered_words, key=lambda w: (accuracy(w), random.random()))
            self.deck = dedup_by_english(ordered)[:session_size]
        # --- Weighted Selection Based on Stats ---
        elif self._stats_manager:
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

            # Oversample, then keep unique by id AND by English, then trim.
            picked = random.choices(filtered_words, weights=weights, k=session_size * 3)
            seen_id, by_id = set(), []
            for card in picked:
                if card['id'] not in seen_id:
                    seen_id.add(card['id'])
                    by_id.append(card)
            self.deck = dedup_by_english(by_id)[:session_size]
        else:
            self.deck = dedup_by_english(random.sample(filtered_words, len(filtered_words)))[:session_size]

        print(f"[SHUFFLE] Created session deck with {len(self.deck)} cards (hardest_first={hardest_first}):")
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
            """Sort by the group prefix (alphabetical) then the sub-range start
            (numeric) — deterministic across launches. Sorting only by the first
            number made every '... (1-15)' group tie, so their order came from the
            set's iteration and shuffled every run."""
            match = re.match(r'^(.*?)\s*\((\d+)', topic)
            if match:
                return (match.group(1).strip().lower(), int(match.group(2)))
            return (topic.lower(), 0)

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

    def add_words_to_topic(self, category, pairs, default_complexity=0.5,
                           update_existing=False):
        """Adds several words under one topic/category at once.

        `pairs` is an iterable of dicts with at least 'english' (and usually
        'uzbek'). Optional per-row keys: 'hint', 'definition', 'grammar_pattern',
        'synonyms' (a list, or a comma-separated string).

        Deduplication is PER TOPIC: a word is skipped only if it already exists in
        THIS SAME category. The same English word may live in several topics (e.g.
        "Cosy" in both a house topic and a feelings topic) so every topic downloads
        complete instead of losing words that happen to appear elsewhere.

        With update_existing=True (used when re-downloading a cloud topic), a word
        already in this category is refreshed in place instead of skipped — its
        translation/hint/etc. are updated while its id and answer stats are kept —
        so content fixes in the cloud reach decks that already have it.

        Saves once. Returns how many words were added or updated.
        """
        category = (category or '').strip()
        # Dedup only against words already in THIS topic, not the whole vocabulary.
        in_category = {w['english'].lower(): w for w in self.words
                       if (w.get('category') or '').strip() == category}
        changed = 0
        for row in pairs:
            english = (row.get('english') or '').strip()
            if not english:
                continue
            uzbek = (row.get('uzbek') or '').strip()
            hint = (row.get('hint') or '').strip() or None
            definition = (row.get('definition') or '').strip() or None
            grammar_pattern = (row.get('grammar_pattern') or '').strip() or None
            synonyms = row.get('synonyms') or []
            if isinstance(synonyms, str):
                synonyms = [s.strip() for s in synonyms.split(',') if s.strip()]
            existing_word = in_category.get(english.lower())
            if existing_word is not None:
                # Same word, same topic → refresh it (update) or leave it (add).
                if update_existing:
                    fields = {'uzbek': uzbek, 'hint': hint, 'definition': definition,
                              'grammar_pattern': grammar_pattern, 'synonyms': synonyms}
                    if any(existing_word.get(k) != v for k, v in fields.items()):
                        existing_word.update(fields)
                        changed += 1
                continue  # never duplicate a word within the same topic
            new_word = {
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
            }
            self.words.append(new_word)
            in_category[english.lower()] = new_word
            changed += 1
        if changed:
            self.save_words()
        print(f"Added/updated {changed} word(s) in topic '{category}'.")
        return changed

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
        """Generates multiple-choice options for a card. Distractors are kept close to
        the card: first its exact sub-range, then the whole topic (e.g. all of
        'Inter 4A 4B'), then the topics selected for this session, and only as a last
        resort every word — so a small topic never pulls options from unrelated ones."""
        import re

        def group_of(cat):
            m = re.match(r'^(.*?)\s*\(', cat or '')
            return (m.group(1).strip() if m else (cat or '')).lower()

        card_category = correct_card.get('category')
        card_group = group_of(card_category)
        print(f"[OPTIONS] Generating options for: {correct_card['english']} (cat={card_category})")

        # 1) exact sub-range → 2) whole topic → 3) session topics → 4) everything.
        same_category_words = [w for w in self.words if w.get('category') == card_category]
        if len(same_category_words) < 4:
            same_category_words = [w for w in self.words
                                   if group_of(w.get('category')) == card_group]
        if len(same_category_words) < 4 and self._active_topics:
            same_category_words = [w for w in self.words
                                   if w.get('category') in self._active_topics]
        if len(same_category_words) < 4:
            same_category_words = self.words
        if not same_category_words:
            return []

        correct_answer = (correct_card.get(language) or '').strip()
        options = {correct_answer} if correct_answer else set()

        # Get distractors — skip words whose answer value is empty. Many words
        # (e.g. the SAT sets) have english + definition but NO uzbek translation,
        # and picking one as a distractor produced a blank option like the empty
        # 4th choice in ['Very big', 'yirtmoq', 'Ketma-ketlik', ''].
        attempts = 0
        while len(options) < 4 and attempts < 50:
            attempts += 1
            random_word = random.choice(same_category_words)
            value = (random_word.get(language) or '').strip()
            if value and value not in options:
                options.add(value)

        shuffled_options = list(options)
        random.shuffle(shuffled_options)
        print(f"[OPTIONS] Generated options: {shuffled_options}")
        return shuffled_options
