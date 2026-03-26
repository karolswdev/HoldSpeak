# HoldSpeak TUI Demo
# Run with: vhs scripts/tui_demo.tape
#
# This tape launches the TUI and captures key states.
# Requires: holdspeak installed and configured

Output docs/screenshots/tui_demo.gif

Set Shell "bash"
Set FontSize 13
Set Width 1100
Set Height 700
Set Theme "Catppuccin Mocha"
Set Padding 10
Set Framerate 20

# Start in project directory
Type "cd ~/Tools/HoldSpeak && clear"
Enter
Sleep 500ms

# Launch TUI (it will show loading then idle state)
Type "uv run holdspeak"
Enter

# Wait for model to load and TUI to appear
Sleep 5s

# Show idle state
Sleep 2s

# Start a meeting
Type "m"
Sleep 3s

# Edit meeting metadata
Type "e"
Sleep 1500ms

# Type title
Type "Weekly Team Sync"
Sleep 500ms

# Tab to tags
Tab
Sleep 300ms
Type "team, weekly, sync"
Sleep 500ms

# Save (Enter on Save button)
Tab
Enter
Sleep 2s

# Show bookmark
Type "b"
Sleep 2s

# Show transcript
Type "t"
Sleep 2s

# Close transcript
Escape
Sleep 1s

# Stop meeting
Type "m"
Sleep 2s

# Show history
Type "h"
Sleep 2s
Escape
Sleep 1s

# Show action items
Type "a"
Sleep 2s
Escape
Sleep 1s

# Settings
Type "s"
Sleep 2s
Escape
Sleep 1s

# Quit
Type "q"
Sleep 1s
