#!/usr/bin/env python3
"""List declared configuration fields without loading a user's configuration."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def extract(path: Path) -> list[dict]:
    text = path.read_text()
    rows = []
    for cls in ast.parse(text).body:
        if not isinstance(cls, ast.ClassDef):
            continue
        if not any(ast.unparse(decorator).startswith('dataclass') for decorator in cls.decorator_list):
            continue
        for field in cls.body:
            if not isinstance(field, ast.AnnAssign) or not isinstance(field.target, ast.Name):
                continue
            rows.append({
                'class': cls.name,
                'field': field.target.id,
                'type': ast.unparse(field.annotation),
                'default_expression': ast.unparse(field.value) if field.value else None,
                'path': str(path.relative_to(ROOT)),
                'line': field.lineno,
            })
    return rows


def generate() -> dict[str, str]:
    rows = [row for path in sorted((ROOT / 'holdspeak/config').glob('*.py')) for row in extract(path)]
    snapshot = json.loads((ROOT / 'docs/internal/philo/snapshot.json').read_text())['commit']
    limits = ('Dataclass declarations only. Defaults are source expressions, not evaluated values. '
              'Load coercion, migrations, validation, environment variables and database-backed '
              'settings can change effective behavior. This is not a complete runtime configuration schema.')
    data = {'snapshot': snapshot, 'generator': 'scripts/philo_config_reference.py', 'limits': limits, 'fields': rows}
    lines = ['# Configuration declaration reference', '', '<!-- GENERATED: scripts/philo_config_reference.py -->', '',
             f'Source snapshot: `{snapshot}`.', '', limits, '',
             'The hub configuration shell is [`Config`](../holdspeak/config/core.py). '
             'Its load/save path composes the section classes below. Use Settings for supported changes. '
             'Do not paste credentials into generated examples. Retired compatibility fields are retained only in the machine inventory.', '',
             '| Class.field | Type | Declared default | Source |', '| --- | --- | --- | --- |']
    for row in rows:
        # Retired compatibility fields remain in the machine inventory, not setup guidance.
        if row['field'] == 'inference_target_id':
            continue
        esc = lambda value: str(value).replace('|', '\\|').replace('`', "'").replace('\n', ' ')
        lines.append(f"| `{row['class']}.{row['field']}` | `{esc(row['type'])}` | `{esc(row['default_expression'])}` | [{row['path']}:{row['line']}](../{row['path']}) |")
    return {'docs/generated/configuration-fields.json': json.dumps(data, indent=2) + '\n',
            'docs/CONFIGURATION_REFERENCE.md': '\n'.join(lines) + '\n'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for relative, text in generate().items():
        path = ROOT / relative
        if args.check:
            if not path.exists() or path.read_text() != text:
                raise SystemExit(f'Configuration reference drift: {relative}')
        else:
            path.write_text(text)
    print('Configuration declaration reference is current')


if __name__ == '__main__':
    main()
