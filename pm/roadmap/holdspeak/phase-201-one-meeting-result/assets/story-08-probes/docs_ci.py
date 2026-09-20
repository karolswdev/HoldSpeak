"""Run the eleven documentation CI commands with the invoking interpreter."""
import glob
import subprocess
import sys

commands = [
    ["-m", "unittest", "discover", "-s", "tests/unit", "-p", "test_docs_navigation.py"],
    ["scripts/check_docs.py"],
    ["scripts/check_docs.py", *[
        path
        for pattern in [
            "docs/internal/philo/*.md",
            "docs/internal/philo/adr/*.md",
            "docs/internal/philo/checks/*.md",
            "docs/internal/philo/visuals/README.md",
            "docs/internal/philo/desktop-prototypes/README.md",
            "agent/skills/*/SKILL.md",
        ]
        for path in sorted(glob.glob(pattern))
    ]],
    ["scripts/philo_repository_census.py", "--check"],
    ["scripts/philo_api_reference.py", "--check"],
    ["scripts/philo_boundary_census.py", "--check"],
    ["scripts/philo_doctor_reference.py", "--check"],
    ["scripts/philo_config_reference.py", "--check"],
    ["scripts/validate_architecture.py"],
    ["scripts/generate_capability_docs.py", "--check"],
    ["scripts/check_doc_coverage.py", "--check"],
]
print("Python:", sys.version, flush=True)
print("T1:", subprocess.check_output(["git", "write-tree"], text=True).strip(), flush=True)
for command in commands:
    print("COMMAND:", sys.executable, *command, flush=True)
    subprocess.run([sys.executable, *command], check=True)
print("All eleven documentation CI commands passed.", flush=True)
