# HoldSpeak Demo
# Run with: vhs demo.tape
#
# This tape demonstrates HoldSpeak's CLI features.
# For TUI demos, use the SVG screenshots in docs/screenshots/

Output docs/demo.gif

Set Shell "bash"
Set FontSize 14
Set Width 1000
Set Height 600
Set Theme "Catppuccin Mocha"
Set Padding 20
Set Framerate 24

# ============================================================
# Intro
# ============================================================

Type "# HoldSpeak - Voice Typing for Mac"
Enter
Sleep 500ms
Type "# Hold a key, speak, release to type"
Enter
Sleep 2s
Ctrl+L

# ============================================================
# Show help
# ============================================================

Type "uv run holdspeak --help"
Enter
Sleep 3s

Ctrl+L
Sleep 500ms

# ============================================================
# Meeting history
# ============================================================

Type "# Browse meeting history"
Enter
Sleep 500ms

Type "uv run holdspeak history --limit 5"
Enter
Sleep 3s

Ctrl+L
Sleep 500ms

# ============================================================
# Action items
# ============================================================

Type "# View action items across meetings"
Enter
Sleep 500ms

Type "uv run holdspeak actions"
Enter
Sleep 3s

Ctrl+L
Sleep 500ms

# ============================================================
# Meeting setup check
# ============================================================

Type "# Check BlackHole setup for meeting mode"
Enter
Sleep 500ms

Type "uv run holdspeak meeting --setup"
Enter
Sleep 3s

Ctrl+L
Sleep 500ms

# ============================================================
# Modes overview
# ============================================================

Type "# Available modes:"
Enter
Sleep 300ms
Type "#   holdspeak          - TUI mode (default)"
Enter
Sleep 300ms
Type "#   holdspeak menubar  - Menu bar mode"
Enter
Sleep 300ms
Type "#   holdspeak meeting  - Meeting capture mode"
Enter
Sleep 300ms
Type "#   holdspeak history  - Browse past meetings"
Enter
Sleep 300ms
Type "#   holdspeak actions  - Manage action items"
Enter
Sleep 2s

Ctrl+L
Sleep 500ms

# ============================================================
# TUI keybindings
# ============================================================

Type "# TUI Keybindings:"
Enter
Sleep 300ms
Type "#   Option+R  - Hold to record, release to transcribe"
Enter
Sleep 300ms
Type "#   m         - Toggle meeting mode"
Enter
Sleep 300ms
Type "#   e         - Edit meeting title/tags"
Enter
Sleep 300ms
Type "#   b         - Add bookmark"
Enter
Sleep 300ms
Type "#   t         - View transcript"
Enter
Sleep 300ms
Type "#   s         - Settings"
Enter
Sleep 300ms
Type "#   h         - Meeting history"
Enter
Sleep 300ms
Type "#   a         - Action items"
Enter
Sleep 300ms
Type "#   ?         - Help screen"
Enter
Sleep 300ms
Type "#   q         - Quit"
Enter
Sleep 3s

# ============================================================
# Final
# ============================================================

Ctrl+L
Type "# Try it: uv run holdspeak"
Enter
Sleep 2s
