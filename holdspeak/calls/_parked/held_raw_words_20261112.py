# Parked: held arguments are disclosed only by the tool declaration.

def raw_hold_words(tool, args, hold_words):
    if tool == "nudge.send" and args.get("text"):
        return "Post this nudge on GitHub: " + str(args["text"])[:160]
    data = args.get("data") if isinstance(args.get("data"), dict) else {}
    label = str(args.get("task") or args.get("title") or data.get("title") or "").strip()
    if label:
        return f"{hold_words(tool)}: {label[:120]}"
