#!/usr/bin/env python3
"""Generate Glintstone academic invite codes.

Codes are in XXXX-XXXX-XXXX format (12 alphanumeric chars, uppercase,
hyphen-separated). The script outputs the codes and the SQL to insert them.
It does NOT connect to the database directly — that would bypass the two-tier
rule and require credentials on whatever machine runs the script.

Usage:
    python ops/tools/generate_invite.py --label "Cohort 1 - Dr. Al-Rashid" --count 5
    python ops/tools/generate_invite.py --count 1 --no-sql

The SQL output is safe to pipe directly into psql:
    python ops/tools/generate_invite.py --label "Test" --count 3 | grep INSERT | psql $DATABASE_URL
"""

import argparse
import secrets
import string
import sys


_CHARS = string.ascii_uppercase + string.digits
# Remove visually ambiguous characters (O/0, I/1) to reduce copy errors
_CHARS = _CHARS.translate(str.maketrans("", "", "O0I1"))


def generate_code() -> str:
    """Return a single XXXX-XXXX-XXXX invite code."""
    parts = ["".join(secrets.choice(_CHARS) for _ in range(4)) for _ in range(3)]
    return "-".join(parts)


def sql_escape(value: str) -> str:
    return value.replace("'", "''")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Glintstone scholar invite codes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--label", default="", help="Batch label (e.g. 'Cohort 1')")
    parser.add_argument(
        "--count", type=int, default=1, help="Number of codes to generate"
    )
    parser.add_argument(
        "--no-sql", action="store_true", help="Suppress SQL INSERT output"
    )
    args = parser.parse_args()

    if args.count < 1:
        print("Error: --count must be >= 1", file=sys.stderr)
        sys.exit(1)

    codes = [generate_code() for _ in range(args.count)]

    print(f"Generated {args.count} invite code(s):\n")
    for code in codes:
        print(f"  {code}")

    print("\nRegistration link(s):")
    for code in codes:
        print(f"  https://app.glintstone.org/auth/register?code={code}")

    if not args.no_sql:
        label_sql = f"'{sql_escape(args.label)}'" if args.label else "NULL"
        print("\nSQL to insert (run as wittkensis against the Glintstone DB):")
        for code in codes:
            print(
                f"  INSERT INTO invite_codes (code, label) "
                f"VALUES ('{sql_escape(code)}', {label_sql});"
            )


if __name__ == "__main__":
    main()
