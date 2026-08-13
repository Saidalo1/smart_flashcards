"""Tiny in-app localization: ru / uz / en string tables + tr().

The chosen language is global (all profiles share it) and persisted in the data
dir, so the very first screen (profile picker) can already be localized before
any profile is selected. Use tr('key', **fmt) everywhere a user-facing string
is shown; missing keys fall back to Russian, then to the key itself.
"""
from app_paths import get_data_dir

LANGUAGES = {'ru': 'Русский', 'uz': "O'zbekcha", 'en': 'English'}
DEFAULT_LANG = 'ru'

_state = {'lang': DEFAULT_LANG}


STRINGS = {
    # ---------------- Startup / profile picker ----------------
    'welcome_title':      {'ru': '👋 Добро пожаловать!',      'uz': '👋 Xush kelibsiz!',                  'en': '👋 Welcome!'},
    'welcome_subtitle':   {'ru': 'Выберите профиль или создайте новый', 'uz': 'Profil tanlang yoki yangi yarating', 'en': 'Choose a profile or create a new one'},
    'new_profile':        {'ru': '✨ Новый профиль',          'uz': '✨ Yangi profil',                    'en': '✨ New profile'},
    'enter_name':         {'ru': 'Введите имя...',            'uz': 'Ismni kiriting...',                  'en': 'Enter a name...'},
    'create':             {'ru': 'Создать',                   'uz': 'Yaratish',                           'en': 'Create'},
    'choose_topics':      {'ru': '📚 Выберите темы для изучения', 'uz': "📚 O'rganish uchun mavzularni tanlang", 'en': '📚 Choose topics to study'},
    'add_topic':          {'ru': '➕ Добавить тему',          'uz': "➕ Mavzu qo'shish",                  'en': '➕ Add topic'},
    'study_mode':         {'ru': '🎯 Режим обучения',         'uz': "🎯 O'rganish rejimi",                'en': '🎯 Study mode'},
    'continue':           {'ru': '▶️ Продолжить',             'uz': '▶️ Davom etish',                     'en': '▶️ Continue'},
    'language':           {'ru': 'Язык',                      'uz': 'Til',                                'en': 'Language'},
    'empty_topics':       {'ru': 'Пока нет слов. Нажмите «➕ Добавить тему», чтобы создать первую тему.',
                           'uz': "Hozircha so'zlar yo'q. Birinchi mavzuni yaratish uchun «➕ Mavzu qo'shish» tugmasini bosing.",
                           'en': 'No words yet. Click «➕ Add topic» to create your first topic.'},
    'last_topic':         {'ru': '↩ Последняя тема: {topic}', 'uz': '↩ Oxirgi mavzu: {topic}',            'en': '↩ Last topic: {topic}'},
    'words_n':            {'ru': '{n} слов',                  'uz': "{n} so'z",                           'en': '{n} words'},
    'mode_adaptive':      {'ru': '🧠 Адаптивный (рекомендуемый)', 'uz': '🧠 Moslashuvchan (tavsiya etiladi)', 'en': '🧠 Adaptive (recommended)'},
    'mode_translation':   {'ru': '🌐 Только перевод',         'uz': '🌐 Faqat tarjima',                   'en': '🌐 Translation only'},
    'mode_definition':    {'ru': '📝 Только определения',     'uz': "📝 Faqat ta'riflar",                 'en': '📝 Definitions only'},
    'mode_synonym':       {'ru': '🔀 Только синонимы',        'uz': '🔀 Faqat sinonimlar',                'en': '🔀 Synonyms only'},
    'err_title':          {'ru': 'Ошибка',                    'uz': 'Xato',                               'en': 'Error'},
    'err_select_profile': {'ru': 'Выберите или создайте профиль!', 'uz': 'Profil tanlang yoki yarating!', 'en': 'Select or create a profile!'},
    'err_enter_name':     {'ru': 'Введите имя профиля!',      'uz': 'Profil nomini kiriting!',            'en': 'Enter a profile name!'},
    'err_profile_exists': {'ru': "Профиль '{name}' уже существует!", 'uz': "'{name}' profili allaqachon mavjud!", 'en': "Profile '{name}' already exists!"},
    'del_profile_btn':    {'ru': '🗑 Удалить профиль',      'uz': "🗑 Profilni o'chirish",              'en': '🗑 Delete profile'},
    'del_profile_confirm':{'ru': "Удалить профиль '<b>{name}</b>' и все его данные?",
                           'uz': "'<b>{name}</b>' profili va barcha ma'lumotlari o'chirilsinmi?",
                           'en': "Delete profile '<b>{name}</b>' and all its data?"},
    'del_topic':          {'ru': '🗑 Удалить тему',            'uz': "🗑 Mavzuni o'chirish",               'en': '🗑 Delete topic'},
    'del_topic_confirm':  {'ru': 'Удалить тему «<b>{name}</b>» и все её слова?',
                           'uz': "«<b>{name}</b>» mavzusi va uning barcha so'zlari o'chirilsinmi?",
                           'en': 'Delete the topic "<b>{name}</b>" and all its words?'},
    'update_title':       {'ru': 'Обновление',                 'uz': 'Yangilanish',                        'en': 'Update'},
    'update_available':   {'ru': 'Доступна новая версия {version}. Обновить сейчас?',
                           'uz': 'Yangi versiya {version} mavjud. Hozir yangilansinmi?',
                           'en': 'A new version {version} is available. Update now?'},
    'update_failed':      {'ru': 'Не удалось загрузить обновление. Попробуйте позже.',
                           'uz': "Yangilanishni yuklab bo'lmadi. Keyinroq urinib ko'ring.",
                           'en': 'Could not download the update. Please try again later.'},
    'update_downloading': {'ru': 'Загрузка обновления…',       'uz': 'Yangilanish yuklanmoqda…',           'en': 'Downloading update…'},

    # ---------------- Cloud catalog ----------------
    'catalog_btn':        {'ru': '☁ Из облака',               'uz': '☁ Bulutdan',                         'en': '☁ From cloud'},
    'catalog_title':      {'ru': '☁ Каталог тем',             'uz': '☁ Mavzular katalogi',                'en': '☁ Topic catalog'},
    'catalog_subtitle':   {'ru': 'Скачайте готовые темы прямо в свой словарь',
                           'uz': "Tayyor mavzularni to'g'ridan-to'g'ri lug'atingizga yuklab oling",
                           'en': 'Download ready-made topics straight into your vocabulary'},
    'catalog_search_ph':  {'ru': '🔍 Поиск темы…',            'uz': '🔍 Mavzu qidirish…',                 'en': '🔍 Search topics…'},
    'catalog_loading':    {'ru': 'Загрузка каталога…',        'uz': 'Katalog yuklanmoqda…',               'en': 'Loading catalog…'},
    'catalog_offline':    {'ru': 'Не удалось загрузить каталог. Проверьте подключение к интернету.',
                           'uz': "Katalogni yuklab bo'lmadi. Internet aloqasini tekshiring.",
                           'en': 'Could not load the catalog. Check your internet connection.'},
    'catalog_retry':      {'ru': '↻ Повторить',               'uz': '↻ Qayta urinish',                    'en': '↻ Retry'},
    'catalog_empty':      {'ru': 'Каталог пуст.',             'uz': "Katalog bo'sh.",                     'en': 'The catalog is empty.'},
    'catalog_add':        {'ru': '➕ Добавить',               'uz': "➕ Qo'shish",                         'en': '➕ Add'},
    'catalog_added':      {'ru': '✓ Добавлено',               'uz': "✓ Qo'shildi",                        'en': '✓ Added'},
    'catalog_downloading':{'ru': '⏳ Загрузка…',              'uz': '⏳ Yuklanmoqda…',                     'en': '⏳ Downloading…'},
    'catalog_add_failed': {'ru': 'Не удалось загрузить тему. Попробуйте позже.',
                           'uz': "Mavzuni yuklab bo'lmadi. Keyinroq urinib ko'ring.",
                           'en': 'Could not download the topic. Please try again later.'},
    'catalog_added_toast':{'ru': 'Тема «{name}» добавлена ({n} слов).',
                           'uz': "«{name}» mavzusi qo'shildi ({n} so'z).",
                           'en': 'Topic "{name}" added ({n} words).'},
    'catalog_done':       {'ru': 'Готово',                    'uz': 'Tayyor',                             'en': 'Done'},
    'catalog_words_n':    {'ru': '{n} слов',                  'uz': "{n} so'z",                           'en': '{n} words'},

    # ---------------- Tray menu ----------------
    'tray_manage':        {'ru': '📚 Управление...',          'uz': '📚 Boshqaruv...',                    'en': '📚 Manage...'},
    'tray_shuffle':       {'ru': '🔀 Перемешать колоду',      'uz': "🔀 To'plamni aralashtirish",         'en': '🔀 Shuffle deck'},
    'tray_next_card':     {'ru': '▶️ Следующая карточка ({hotkey})', 'uz': '▶️ Keyingi karta ({hotkey})', 'en': '▶️ Next card ({hotkey})'},
    'tray_topics':        {'ru': '📚 Темы',                   'uz': '📚 Mavzular',                        'en': '📚 Topics'},
    'tray_select_all':    {'ru': '✅ Выбрать все',            'uz': '✅ Hammasini tanlash',               'en': '✅ Select all'},
    'tray_no_topics':     {'ru': '(нет тем)',                 'uz': "(mavzular yo'q)",                    'en': '(no topics)'},
    'tray_main_menu':     {'ru': '🏠 Главное меню',           'uz': '🏠 Bosh menyu',                      'en': '🏠 Main menu'},
    'tray_quit':          {'ru': '❌ Выход',                  'uz': '❌ Chiqish',                         'en': '❌ Exit'},
    'topics_updated':     {'ru': 'Темы обновлены',            'uz': 'Mavzular yangilandi',                'en': 'Topics updated'},
    'topics_updated_msg': {'ru': 'Активно тем: {count} · карт в колоде: {deck}', 'uz': "Faol mavzular: {count} · to'plamda: {deck} karta", 'en': 'Active topics: {count} · cards in deck: {deck}'},
    'deck_shuffled':      {'ru': 'Колода перемешана',         'uz': "To'plam aralashtirildi",             'en': 'Deck shuffled'},
    'deck_shuffled_msg':  {'ru': 'Новая сессия из {n} карт!', 'uz': "{n} kartadan yangi sessiya!",        'en': 'New session of {n} cards!'},

    # ---------------- Flashcard ----------------
    'drag_me':            {'ru': '⋮⋮ Перетащи меня ⋮⋮',       'uz': "⋮⋮ Meni sudrab ko'chir ⋮⋮",          'en': '⋮⋮ Drag me ⋮⋮'},
    'prompt_define':      {'ru': 'Определи:',                 'uz': "Ta'rifla:",                          'en': 'Define:'},
    'prompt_synonym':     {'ru': 'Синоним к:',                'uz': 'Sinonim:',                           'en': 'Synonym for:'},
    'prompt_transition':  {'ru': 'Новое слово:',              'uz': "Yangi so'z:",                        'en': 'Transition:'},
    'prompt_translate':   {'ru': 'Переведи:',                 'uz': 'Tarjima qil:',                       'en': 'Translate:'},
    'check_answer':       {'ru': 'Проверить',                 'uz': 'Tekshirish',                         'en': 'Check Answer'},
    'hint_tooltip':       {'ru': 'Подсказка',                 'uz': 'Izoh',                               'en': 'Hint'},
    'delete_card_tooltip':{'ru': 'Удалить эту карточку навсегда', 'uz': "Bu kartani butunlay o'chirish",   'en': 'Delete this card permanently'},
    'ph_translation':     {'ru': 'Введите перевод...',        'uz': 'Tarjimani kiriting...',              'en': 'Enter the translation...'},
    'ph_definition':      {'ru': 'Что означает это слово?...', 'uz': "Bu so'z nimani anglatadi?...",       'en': 'What does this word mean?...'},
    'ph_synonym':         {'ru': 'Введите синоним...',        'uz': 'Sinonim kiriting...',                'en': 'Enter a synonym...'},

    # ---------------- Add-topic dialog ----------------
    'new_topic_title':    {'ru': '➕ Новая тема',             'uz': '➕ Yangi mavzu',                     'en': '➕ New topic'},
    'topic_name':         {'ru': 'Название темы',             'uz': 'Mavzu nomi',                         'en': 'Topic name'},
    'topic_name_ph':      {'ru': 'Выбери существующую тему или впиши новую', 'uz': 'Mavjud mavzuni tanlang yoki yangisini yozing', 'en': 'Pick an existing topic or type a new one'},
    'addtopic_tip':       {'ru': 'Впишите English и перевод (и, по желанию, подсказку). Кнопка ✎ в строке — определение, синонимы, паттерн. Пустые строки игнорируются.',
                           'uz': "English va tarjimani yozing (xohlasangiz — izoh). Qatordagi ✎ tugmasi: ta'rif, sinonimlar, pattern. Bo'sh qatorlar hisobga olinmaydi.",
                           'en': 'Type English and its translation (and optionally a hint). The ✎ button in a row opens definition, synonyms, pattern. Empty rows are ignored.'},
    'col_translation':    {'ru': 'Перевод',                   'uz': 'Tarjima',                            'en': 'Translation'},
    'col_hint':           {'ru': 'Подсказка (необязательно)', 'uz': 'Izoh (ixtiyoriy)',                   'en': 'Hint (optional)'},
    'btn_add_row':        {'ru': '➕ Строка',                 'uz': '➕ Qator',                           'en': '➕ Row'},
    'btn_del_row':        {'ru': '➖ Удалить строку',         'uz': "➖ Qatorni o'chirish",               'en': '➖ Delete row'},
    'cancel':             {'ru': 'Отмена',                    'uz': 'Bekor qilish',                       'en': 'Cancel'},
    'save':               {'ru': '💾 Сохранить',             'uz': '💾 Saqlash',                         'en': '💾 Save'},
    'ok_done':            {'ru': 'Готово',                    'uz': 'Tayyor',                             'en': 'Done'},
    'details_tooltip':    {'ru': 'Определение, синонимы, паттерн', 'uz': "Ta'rif, sinonimlar, pattern",    'en': 'Definition, synonyms, pattern'},
    'err_enter_topic':    {'ru': 'Введите название темы.',    'uz': 'Mavzu nomini kiriting.',             'en': 'Enter a topic name.'},
    'err_add_one_word':   {'ru': 'Добавьте хотя бы одно слово (столбец English).', 'uz': "Kamida bitta so'z qo'shing (English ustuni).", 'en': 'Add at least one word (English column).'},
    'words_added':        {'ru': 'Добавлено слов: {added} в тему «{name}».', 'uz': "«{name}» mavzusiga {added} ta so'z qo'shildi.", 'en': 'Added {added} words to «{name}».'},
    'no_new_words':       {'ru': 'Новых слов не добавлено — возможно, все уже есть в словаре.', 'uz': "Yangi so'z qo'shilmadi — ehtimol, hammasi lug'atda bor.", 'en': 'No new words added — they may already be in the vocabulary.'},

    # ---------------- Word details dialog ----------------
    'word_details':       {'ru': 'Детали слова',              'uz': "So'z tafsilotlari",                  'en': 'Word details'},
    'word_details_of':    {'ru': 'Детали: {word}',            'uz': 'Tafsilot: {word}',                   'en': 'Details: {word}'},
    'def_label':          {'ru': 'Определение (англ.)',       'uz': "Ta'rif (inglizcha)",                 'en': 'Definition (English)'},
    'def_help':           {'ru': 'Короткое объяснение слова на английском. Нужно для режима «Определение».', 'uz': "So'zning inglizcha qisqa izohi. «Ta'rif» rejimi uchun kerak.", 'en': 'A short English explanation. Needed for the Definition mode.'},
    'def_ph':             {'ru': 'напр. to continue having something', 'uz': 'masalan: to continue having something', 'en': 'e.g. to continue having something'},
    'syn_label':          {'ru': 'Синонимы',                  'uz': 'Sinonimlar',                         'en': 'Synonyms'},
    'syn_help':           {'ru': 'Слова с похожим значением. Добавляй по одному кнопкой «＋». Нужны для режима «Синонимы».', 'uz': "Ma'nosi o'xshash so'zlar. «＋» tugmasi bilan bittalab qo'shing. «Sinonimlar» rejimi uchun kerak.", 'en': 'Words with a similar meaning. Add one at a time with «＋». Needed for the Synonyms mode.'},
    'syn_ph':             {'ru': 'впиши синоним и нажми ＋ (или Enter)', 'uz': "sinonim yozing va ＋ bosing (yoki Enter)", 'en': 'type a synonym and press ＋ (or Enter)'},
    'syn_remove_hint':    {'ru': 'Двойной клик по синониму — удалить.', 'uz': "Sinonimni o'chirish uchun ikki marta bosing.", 'en': 'Double-click a synonym to remove it.'},
    'pat_label':          {'ru': 'Паттерн (сочетание)',       'uz': 'Pattern (birikma)',                  'en': 'Pattern (collocation)'},
    'pat_help':           {'ru': 'Как слово обычно сочетается в речи: напр. «avoid doing sth», «depend on sth». Показывается в заголовке карточки.', 'uz': "So'z odatda qanday birikadi: masalan «avoid doing sth», «depend on sth». Karta sarlavhasida ko'rinadi.", 'en': 'How the word usually combines: e.g. «avoid doing sth». Shown in the card title.'},
    'pat_ph':             {'ru': 'напр. avoid doing sth',     'uz': 'masalan: avoid doing sth',           'en': 'e.g. avoid doing sth'},

    # ---------------- Management window ----------------
    'mgmt_title':         {'ru': '📚 Smart Flashcards — Управление', 'uz': '📚 Smart Flashcards — Boshqaruv', 'en': '📚 Smart Flashcards — Manage'},
    'tab_vocab':          {'ru': '📖 Словарь',                'uz': "📖 Lug'at",                          'en': '📖 Vocabulary'},
    'tab_stats':          {'ru': '📊 Статистика',             'uz': '📊 Statistika',                      'en': '📊 Statistics'},
    'tab_settings':       {'ru': '⚙️ Настройки',              'uz': '⚙️ Sozlamalar',                      'en': '⚙️ Settings'},
    'th_level':           {'ru': '📊 Уровень',                'uz': '📊 Daraja',                          'en': '📊 Level'},
    'btn_add':            {'ru': '➕ Добавить',               'uz': "➕ Qo'shish",                        'en': '➕ Add'},
    'btn_edit':           {'ru': '✏️ Редактировать',          'uz': '✏️ Tahrirlash',                      'en': '✏️ Edit'},
    'btn_delete':         {'ru': '🗑️ Удалить',                'uz': "🗑️ O'chirish",                       'en': '🗑️ Delete'},
    'stats_header':       {'ru': '📊 Статистика обучения',    'uz': "📊 O'rganish statistikasi",          'en': '📊 Study statistics'},
    'set_timer_title':    {'ru': '⏱️ Интервал показа карточек', 'uz': "⏱️ Kartalarni ko'rsatish oralig'i", 'en': '⏱️ Card interval'},
    'set_timer_desc':     {'ru': 'Как часто показывать новые карточки (в секундах)', 'uz': "Yangi kartalar qanchalik tez-tez chiqsin (soniyalarda)", 'en': 'How often to show new cards (seconds)'},
    'set_strict_title':   {'ru': '🎯 Строгость проверки ответа', 'uz': "🎯 Javob tekshiruvi qat'iyligi",    'en': '🎯 Answer grading strictness'},
    'set_strict_desc':    {'ru': 'Насколько точно набранный ответ должен совпадать с правильным. Выше — строже (для друзей рекомендуется 70–80%).', 'uz': "Kiritilgan javob to'g'ri javobga qanchalik mos kelishi kerak. Yuqori — qat'iyroq (do'stlar uchun 70–80% tavsiya etiladi).", 'en': 'How closely the typed answer must match. Higher = stricter (70–80% recommended for friends).'},
    'set_semantic':       {'ru': '🧠 Семантическая проверка (принимать синонимы)', 'uz': '🧠 Semantik tekshiruv (sinonimlarni qabul qilish)', 'en': '🧠 Semantic grading (accept synonyms)'},
    'set_semantic_note':  {'ru': 'Выключено — строгая проверка без ИИ: не примет синонимы и не грузит модель (~470 МБ). Изменение применяется после перезапуска.', 'uz': "O'chirilgan — AIsiz qat'iy tekshiruv: sinonimlarni qabul qilmaydi va modelni yuklamaydi (~470 MB). O'zgarish qayta ishga tushgach qo'llanadi.", 'en': 'Off — strict grading without AI: no synonyms, no model download (~470 MB). Applies after restart.'},
    'set_topics_title':   {'ru': '📚 Активные темы',          'uz': '📚 Faol mavzular',                   'en': '📚 Active topics'},
    'set_topics_desc':    {'ru': 'Выберите темы для изучения (если ничего не выбрано — все темы активны)', 'uz': "O'rganish uchun mavzularni tanlang (hech narsa tanlanmasa — barcha mavzular faol)", 'en': 'Choose topics to study (if none selected — all are active)'},
    'set_hotkey_title':   {'ru': '⌨️ Горячая клавиша',        'uz': '⌨️ Tezkor tugma',                    'en': '⌨️ Hotkey'},
    'set_hotkey_desc':    {'ru': 'Клавиша для показа следующей карточки', 'uz': "Keyingi kartani ko'rsatuvchi tugma", 'en': 'Key to show the next card'},
    'set_hotkey_current': {'ru': 'Текущая: {key}',            'uz': 'Joriy: {key}',                       'en': 'Current: {key}'},
    'set_hotkey_btn':     {'ru': '🎹 Назначить клавишу',      'uz': '🎹 Tugma tayinlash',                 'en': '🎹 Set key'},
    'set_position_title': {'ru': '📍 Положение карточки',      'uz': '📍 Karta joylashuvi',                'en': '📍 Card position'},
    'set_position_desc':  {'ru': 'Где показывать карточку на экране', 'uz': "Karta ekranda qayerda chiqsin", 'en': 'Where the card appears on screen'},
    'dup_title':          {'ru': 'Дубликат',                  'uz': 'Takror',                             'en': 'Duplicate'},
    'dup_msg':            {'ru': "Слово '{word}' уже существует.", 'uz': "'{word}' so'zi allaqachon mavjud.", 'en': "The word '{word}' already exists."},
    'err_both_fields':    {'ru': 'Оба поля должны быть заполнены.', 'uz': "Ikkala maydon ham to'ldirilishi kerak.", 'en': 'Both fields must be filled in.'},
    'edit_word_dlg':      {'ru': 'Редактировать слово',       'uz': "So'zni tahrirlash",                  'en': 'Edit word'},
    'stats_th_word':      {'ru': '📝 Слово',                  'uz': "📝 So'z",                            'en': '📝 Word'},
    'stats_th_correct':   {'ru': '✅ Правильно',              'uz': "✅ To'g'ri",                          'en': '✅ Correct'},
    'stats_th_wrong':     {'ru': '❌ Неправильно',            'uz': "❌ Noto'g'ri",                        'en': '❌ Wrong'},
    'stats_th_rate':      {'ru': '📈 Успешность',             'uz': '📈 Muvaffaqiyat',                    'en': '📈 Success rate'},
    'reset_stats_btn':    {'ru': '🗑️ Сбросить статистику',    'uz': '🗑️ Statistikani tozalash',           'en': '🗑️ Reset statistics'},
    'mode_desc':          {'ru': 'Адаптивный — автоматически повышает уровень. Остальные — принудительно тестируют выбранный тип.', 'uz': "Moslashuvchan — darajani avtomatik oshiradi. Boshqalari — tanlangan turni majburiy sinaydi.", 'en': 'Adaptive raises the level automatically. The others force the chosen type.'},
    'unit_sec':           {'ru': ' сек',                      'uz': ' s',                                 'en': ' s'},
    'pos_bottom_right':   {'ru': '↘️ Справа снизу',           'uz': "↘️ Pastda o'ngda",                   'en': '↘️ Bottom-right'},
    'pos_bottom_left':    {'ru': '↙️ Слева снизу',            'uz': '↙️ Pastda chapda',                   'en': '↙️ Bottom-left'},
    'pos_top_right':      {'ru': '↗️ Справа сверху',          'uz': "↗️ Yuqorida o'ngda",                 'en': '↗️ Top-right'},
    'pos_top_left':       {'ru': '↖️ Слева сверху',           'uz': '↖️ Yuqorida chapda',                 'en': '↖️ Top-left'},
    'pos_middle_right':   {'ru': '➡️ Справа по центру',       'uz': "➡️ O'ngda markazda",                 'en': '➡️ Middle-right'},
    'pos_middle_left':    {'ru': '⬅️ Слева по центру',        'uz': '⬅️ Chapda markazda',                 'en': '⬅️ Middle-left'},
    'pos_top_center':     {'ru': '⬆️ Сверху по центру',       'uz': '⬆️ Yuqorida markazda',               'en': '⬆️ Top-center'},
    'pos_bottom_center':  {'ru': '⬇️ Снизу по центру',        'uz': '⬇️ Pastda markazda',                 'en': '⬇️ Bottom-center'},
    'pos_center':         {'ru': '⏺️ По центру',              'uz': '⏺️ Markazda',                        'en': '⏺️ Center'},
    'pos_mouse':          {'ru': '🖱️ У курсора мыши',         'uz': '🖱️ Sichqoncha yonida',               'en': '🖱️ At the mouse cursor'},
    'info_tip_title':     {'ru': '💡 Подсказка',              'uz': '💡 Maslahat',                        'en': '💡 Tip'},
    'hotkey_restart_note':{'ru': 'После смены горячей клавиши нужно перезапустить приложение!', 'uz': "Tezkor tugma o'zgargach, ilovani qayta ishga tushiring!", 'en': 'After changing the hotkey, restart the app!'},
    'press_key':          {'ru': '⏳ Нажмите клавишу...',     'uz': '⏳ Tugmani bosing...',               'en': '⏳ Press a key...'},
    'restart_title':      {'ru': 'Перезапустить?',            'uz': 'Qayta ishga tushirilsinmi?',         'en': 'Restart?'},
    'hotkey_changed_restart': {'ru': 'Горячая клавиша изменена на: {key}\n\nПерезапустить приложение сейчас?', 'uz': "Tezkor tugma {key} ga o'zgartirildi.\n\nIlovani hozir qayta ishga tushirasizmi?", 'en': 'Hotkey changed to: {key}\n\nRestart the app now?'},
    'err_select_edit':    {'ru': 'Выберите слово для редактирования.', 'uz': "Tahrirlash uchun so'z tanlang.", 'en': 'Select a word to edit.'},
    'err_update_failed':  {'ru': 'Не удалось обновить слово.', 'uz': "So'zni yangilab bo'lmadi.",         'en': 'Could not update the word.'},
    'err_select_delete':  {'ru': 'Выберите слово для удаления.', 'uz': "O'chirish uchun so'z tanlang.",   'en': 'Select a word to delete.'},
    'confirm_title':      {'ru': 'Подтверждение',             'uz': 'Tasdiqlash',                         'en': 'Confirm'},
    'confirm_delete_word':{'ru': "Удалить слово '<b>{word}</b>'?", 'uz': "'<b>{word}</b>' so'zi o'chirilsinmi?", 'en': "Delete the word '<b>{word}</b>'?"},
    'word_deleted':       {'ru': "Слово '{word}' удалено.",   'uz': "'{word}' so'zi o'chirildi.",         'en': "Word '{word}' deleted."},
    'reset_stats_title':  {'ru': 'Сброс статистики',          'uz': 'Statistikani tozalash',              'en': 'Reset statistics'},
    'reset_stats_confirm':{'ru': 'Вы уверены? Это действие <b>нельзя отменить</b>!', 'uz': "Ishonchingiz komilmi? Bu amalni <b>bekor qilib bo'lmaydi</b>!", 'en': 'Are you sure? This <b>cannot be undone</b>!'},
    'stats_reset_done':   {'ru': 'Статистика сброшена.',      'uz': 'Statistika tozalandi.',              'en': 'Statistics reset.'},
    'set_position_title2':{'ru': '📍 Позиция карточки',       'uz': '📍 Karta joylashuvi',                'en': '📍 Card position'},
    'set_position_desc2': {'ru': 'Где появляется карточка на экране', 'uz': 'Karta ekranda qayerda paydo bo‘ladi', 'en': 'Where the card appears on screen'},
}


def _lang_file():
    return get_data_dir() / 'language.txt'


def is_language_chosen():
    """True if the user has already picked a language (the file exists).

    Used to show a one-time language picker on the very first launch.
    """
    return _lang_file().exists()


def get_language():
    return _state['lang']


def set_language(lang):
    if lang in STRINGS_LANGS:
        _state['lang'] = lang
        try:
            _lang_file().write_text(lang, encoding='utf-8')
        except Exception:
            pass


def tr(key_id, **fmt):
    table = STRINGS.get(key_id, {})
    text = table.get(_state['lang']) or table.get(DEFAULT_LANG) or key_id
    if fmt:
        try:
            text = text.format(**fmt)
        except Exception:
            pass
    return text


STRINGS_LANGS = set(LANGUAGES.keys())


def _load():
    try:
        lang = _lang_file().read_text(encoding='utf-8').strip()
        if lang in STRINGS_LANGS:
            _state['lang'] = lang
    except Exception:
        pass


_load()
