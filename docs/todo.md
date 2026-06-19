# Smart Flashcards TODO

## High Priority
- [ ] **Fix Global Hotkeys on Linux (Wayland)**:
    - Currently, `pynput` fails on Wayland due to security restrictions (input sniffing is blocked for background apps).
    - **Proposed Solution**: 
        1. Implement `evdev` backend for Linux.
        2. Instruct users to join the `input` group: `sudo usermod -a -G input $USER`.
        3. Fallback to `pynput` only if X11 session is detected.
    - **Alternative**: Explore XDG Desktop Portal (Global Shortcuts) for modern Wayland support without root/input group.

## UI/UX
- [x] Port Settings UI to `QScrollArea` to prevent distortion on smaller screens or Linux.
- [x] Fix font rendering on Linux by adding `Roboto` and `Helvetica Neue` fallbacks.

## Consistency
- [x] Integrate local UI fixes with remote repository updates (resolved merge conflicts).
