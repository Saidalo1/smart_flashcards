"""Global hotkey listener for Linux/Wayland based on evdev (kernel-level input).

Why this exists
---------------
``pynput`` on Linux only supports X11. Under a Wayland session it runs through
XWayland and can therefore only observe key events that are delivered to X11
clients — it never sees keys while another (native Wayland) window is focused,
so a "global" hotkey silently stops working when the app is inactive.

``evdev`` reads input events straight from ``/dev/input/event*`` at the kernel
level, *before* the compositor routes them. That makes hotkey detection truly
global on Wayland (and X11) regardless of which window is focused.

Permissions
-----------
Reading ``/dev/input/event*`` requires membership in the ``input`` group
(``sudo usermod -aG input $USER`` then re-login). No root is needed. Devices are
only *read*, never grabbed, so keystrokes still reach the focused application.
"""
import selectors
import threading

try:
    import evdev
    from evdev import ecodes

    EVDEV_AVAILABLE = True
except Exception:  # ImportError, or evdev present but unusable
    EVDEV_AVAILABLE = False


# Generic modifier name -> set of concrete left/right evdev key codes.
def _modifier_code_sets():
    return {
        'ctrl': {ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL},
        'alt': {ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT},
        'shift': {ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT},
        'win': {ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA},
    }


def _build_keymap():
    """Maps config hotkey token -> tuple of evdev key codes (any of them fires)."""
    if not EVDEV_AVAILABLE:
        return {}

    m = {
        'shift_l': (ecodes.KEY_LEFTSHIFT,),
        'shift_r': (ecodes.KEY_RIGHTSHIFT,),
        'shift': (ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT),
        'ctrl_l': (ecodes.KEY_LEFTCTRL,),
        'ctrl_r': (ecodes.KEY_RIGHTCTRL,),
        'ctrl': (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL),
        'alt_l': (ecodes.KEY_LEFTALT,),
        'alt_r': (ecodes.KEY_RIGHTALT,),
        'alt': (ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT),
        'win_l': (ecodes.KEY_LEFTMETA,),
        'win_r': (ecodes.KEY_RIGHTMETA,),
        'win': (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA),
        'space': (ecodes.KEY_SPACE,),
        'tab': (ecodes.KEY_TAB,),
        'enter': (ecodes.KEY_ENTER,),
        'return': (ecodes.KEY_ENTER,),
        'esc': (ecodes.KEY_ESC,),
        'escape': (ecodes.KEY_ESC,),
        'backspace': (ecodes.KEY_BACKSPACE,),
        'delete': (ecodes.KEY_DELETE,),
        'insert': (ecodes.KEY_INSERT,),
        'home': (ecodes.KEY_HOME,),
        'end': (ecodes.KEY_END,),
        'page_up': (ecodes.KEY_PAGEUP,),
        'page_down': (ecodes.KEY_PAGEDOWN,),
        'up': (ecodes.KEY_UP,),
        'down': (ecodes.KEY_DOWN,),
        'left': (ecodes.KEY_LEFT,),
        'right': (ecodes.KEY_RIGHT,),
        'caps_lock': (ecodes.KEY_CAPSLOCK,),
    }
    for ch in 'abcdefghijklmnopqrstuvwxyz':
        m[ch] = (getattr(ecodes, f'KEY_{ch.upper()}'),)
    for digit in '0123456789':
        m[digit] = (getattr(ecodes, f'KEY_{digit}'),)
    for i in range(1, 25):
        code = getattr(ecodes, f'KEY_F{i}', None)
        if code is not None:
            m[f'f{i}'] = (code,)

    # Remaining tokens the binding UI (management_window.keyPressEvent) can emit:
    # lock/system keys, numpad, and punctuation. Keep this in sync with that
    # method so ANY assignable key resolves to a real evdev code. Uses getattr
    # so a kernel that lacks an exotic code just skips it instead of crashing.
    extra = {
        # Lock / system keys
        'pause': 'KEY_PAUSE',
        'print_screen': 'KEY_SYSRQ',   # PrintScreen is SysRq at the evdev level
        'scroll_lock': 'KEY_SCROLLLOCK',
        'num_lock': 'KEY_NUMLOCK',
        # Numpad
        'num_0': 'KEY_KP0', 'num_1': 'KEY_KP1', 'num_2': 'KEY_KP2',
        'num_3': 'KEY_KP3', 'num_4': 'KEY_KP4', 'num_5': 'KEY_KP5',
        'num_6': 'KEY_KP6', 'num_7': 'KEY_KP7', 'num_8': 'KEY_KP8',
        'num_9': 'KEY_KP9',
        'num_decimal': 'KEY_KPDOT', 'num_divide': 'KEY_KPSLASH',
        'num_multiply': 'KEY_KPASTERISK', 'num_subtract': 'KEY_KPMINUS',
        'num_add': 'KEY_KPPLUS', 'num_enter': 'KEY_KPENTER',
        # Punctuation / symbols (main keyboard block)
        'minus': 'KEY_MINUS',
        'plus': 'KEY_EQUAL',   # UI stores '=' key as "plus"
        '[': 'KEY_LEFTBRACE', ']': 'KEY_RIGHTBRACE',
        ';': 'KEY_SEMICOLON', "'": 'KEY_APOSTROPHE',
        ',': 'KEY_COMMA', '.': 'KEY_DOT', '/': 'KEY_SLASH',
        '\\': 'KEY_BACKSLASH', '`': 'KEY_GRAVE',
    }
    for token, attr in extra.items():
        code = getattr(ecodes, attr, None)
        if code is not None:
            m[token] = (code,)
    return m


def _find_keyboard_devices(target_codes):
    """Returns opened InputDevices that can emit our target/modifier keys."""
    wanted = set(target_codes)
    for mod_codes in _modifier_code_sets().values():
        wanted |= mod_codes

    devices = []
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
        except (OSError, PermissionError):
            continue
        key_caps = set(dev.capabilities().get(ecodes.EV_KEY, []))
        # A real keyboard exposes the letter block; also accept any device that
        # carries one of the keys we actually care about (covers wireless
        # dongles that split modifiers onto a separate node).
        looks_like_keyboard = ecodes.KEY_A in key_caps and ecodes.KEY_Z in key_caps
        if looks_like_keyboard or (key_caps & wanted):
            devices.append(dev)
        else:
            dev.close()
    return devices


class EvdevHotkeyListener:
    """Global hotkey listener that reads /dev/input via evdev in a daemon thread.

    Parses the same hotkey syntax used elsewhere in the app: single keys
    (``f7``, ``k``), single left/right modifiers (``shift_r``, ``ctrl_l``),
    generic single modifiers (``shift``) and combos (``ctrl+alt+k``).
    """

    def __init__(self, hotkey_str, callback):
        self._callback = callback
        self._devices = []
        self._selector = None
        self._thread = None
        self._running = False
        self._pressed = set()          # currently held key codes
        self._required_mods = []        # list of code-sets; each must be held
        self._target_codes = ()         # key codes that trigger the hotkey
        self._parse(hotkey_str)

    def _parse(self, hotkey_str):
        keymap = _build_keymap()
        generic_mods = {'ctrl', 'alt', 'shift', 'win'}
        mod_sets = _modifier_code_sets()

        parts = [p.strip() for p in hotkey_str.lower().split('+') if p.strip()]
        if len(parts) <= 1:
            # Single key or single modifier: the token itself is the trigger.
            target = parts[0] if parts else ''
        else:
            # Combo: generic tokens are required modifiers, the rest is target.
            self._required_mods = [mod_sets[p] for p in parts if p in generic_mods]
            targets = [p for p in parts if p not in generic_mods]
            target = targets[0] if targets else parts[-1]

        self._target_codes = keymap.get(target, ())

    def start(self):
        """Starts the listener. Returns True on success, False otherwise."""
        if not EVDEV_AVAILABLE or not self._target_codes:
            return False
        try:
            self._devices = _find_keyboard_devices(self._target_codes)
        except Exception:
            self._devices = []
        if not self._devices:
            return False

        self._selector = selectors.DefaultSelector()
        for dev in self._devices:
            self._selector.register(dev, selectors.EVENT_READ)

        self._running = True
        self._thread = threading.Thread(target=self._run, name='evdev-hotkey', daemon=True)
        self._thread.start()
        return True

    def _run(self):
        while self._running:
            try:
                ready = self._selector.select(timeout=0.5)
            except OSError:
                break
            for key, _mask in ready:
                device = key.fileobj
                try:
                    for event in device.read():
                        if event.type == ecodes.EV_KEY:
                            self._handle(event)
                except OSError:
                    # Device disconnected; drop it and keep going.
                    try:
                        self._selector.unregister(device)
                    except (KeyError, ValueError):
                        pass

    def _handle(self, event):
        code = event.code
        if event.value == 1:  # key down
            self._pressed.add(code)
            if code in self._target_codes and self._modifiers_satisfied():
                self._callback()
        elif event.value == 0:  # key up
            self._pressed.discard(code)
        # value == 2 is autorepeat and is intentionally ignored.

    def _modifiers_satisfied(self):
        return all(bool(mod_set & self._pressed) for mod_set in self._required_mods)

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        if self._selector is not None:
            try:
                self._selector.close()
            except Exception:
                pass
        for dev in self._devices:
            try:
                dev.close()
            except Exception:
                pass
        self._devices = []
