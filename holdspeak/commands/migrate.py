"""Migration subcommand for HoldSpeak."""

from __future__ import annotations

from ..db_migration import list_json_meetings, migrate_json_meetings


def run_migrate_command(args) -> None:
    """Handle the `migrate` subcommand."""
    if args.dry_run:
        json_meetings = list_json_meetings()
        if not json_meetings:
            print("No JSON meeting files found to migrate.")
            return

        print(f"Found {len(json_meetings)} JSON meeting file(s):\n")
        for path, meeting_id, started_at in json_meetings:
            date_str = started_at.strftime("%Y-%m-%d %H:%M")
            print(f"  {meeting_id[:12]} ({date_str}) - {path.name}")

        print("\nRun 'holdspeak migrate' (without --dry-run) to import these.")
        return

    print("Migrating JSON meetings to database...")
    migrated, skipped, errors = migrate_json_meetings()

    print("\nMigration complete:")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped (already exist): {skipped}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for err in errors:
            print(f"    - {err}")
