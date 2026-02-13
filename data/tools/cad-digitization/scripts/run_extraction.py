#!/usr/bin/env python3
"""
Run langextract on CAD text files.

Usage:
    python run_extraction.py --input text/cad_g.txt --output output/cad_g.jsonl
    python run_extraction.py --all --model gemini-2.5-pro

This script:
1. Loads the extraction configuration
2. Reads few-shot examples
3. Runs langextract with source grounding
4. Outputs JSONL and HTML visualization
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Check for API key
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    # Try loading from .env file in parent directory
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("GOOGLE_API_KEY="):
                    GOOGLE_API_KEY = line.split("=", 1)[1].strip()
                    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
                    break


def check_langextract():
    """Check if langextract is available and working."""
    try:
        import langextract
        return True
    except ImportError:
        return False


def load_examples(examples_path: Path) -> list:
    """Load few-shot examples from JSON file."""
    if not examples_path.exists():
        return []

    with open(examples_path) as f:
        data = json.load(f)
        return data.get("examples", [])


def run_extraction_mock(input_path: Path, output_path: Path, html_path: Path, model: str):
    """
    Mock extraction for testing when langextract isn't available.

    This demonstrates the expected output format.
    """
    print(f"  [MOCK MODE] langextract not available")
    print(f"  Reading: {input_path}")

    # Read input text
    text = input_path.read_text(encoding='utf-8')
    lines = text.split('\n')

    # Simple mock extraction - find potential headwords
    entries = []
    import re
    headword_pattern = re.compile(
        r'^([a-zšṣṭḫāēīū][a-zšṣṭḫāēīū\-\']+)\s+(s\.|v\.|adj\.|adv\.)',
        re.IGNORECASE
    )

    for i, line in enumerate(lines):
        match = headword_pattern.match(line.strip())
        if match:
            entry = {
                "headword": match.group(1),
                "part_of_speech": match.group(2),
                "source_line": i + 1,
                "meanings": [],
                "logograms": [],
                "cross_references": [],
            }
            entries.append(entry)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    # Write simple HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>CAD Extraction Results (Mock)</title>
    <style>
        body {{ font-family: sans-serif; margin: 2em; }}
        .entry {{ margin: 1em 0; padding: 1em; border: 1px solid #ccc; }}
        .headword {{ font-weight: bold; font-size: 1.2em; }}
        .pos {{ color: #666; }}
    </style>
</head>
<body>
    <h1>CAD Extraction Results (Mock Mode)</h1>
    <p>This is a mock extraction. Install langextract for real extraction.</p>
    <p>Found {len(entries)} potential entries.</p>
    {"".join(f'<div class="entry"><span class="headword">{e["headword"]}</span> <span class="pos">{e["part_of_speech"]}</span></div>' for e in entries[:50])}
</body>
</html>
"""
    html_path.write_text(html_content, encoding='utf-8')

    return len(entries)


def run_extraction_real(input_path: Path, output_path: Path, html_path: Path,
                        model: str, examples: list, batch: bool = False):
    """
    Run actual langextract extraction.
    """
    import langextract
    from langextract import extract, Config

    print(f"  Model: {model}")
    print(f"  Examples: {len(examples)}")
    print(f"  Batch mode: {batch}")

    # Load configuration
    sys.path.insert(0, str(Path(__file__).parent.parent / "config"))
    from extraction_config import EXTRACTION_CONFIG, CADEntry

    # Create langextract config
    config = Config(
        model=model,
        temperature=0.1,
        examples=examples,
        entity_types=[CADEntry],
        system_prompt=EXTRACTION_CONFIG["extraction_prompt"],
    )

    # Read input text
    text = input_path.read_text(encoding='utf-8')

    print(f"  Input size: {len(text):,} characters")
    print(f"  Extracting...")

    # Run extraction
    results = extract(
        text=text,
        config=config,
        output_format="jsonl",
        html_output=str(html_path),
    )

    # Write results
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in results:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    return len(results)


def main():
    parser = argparse.ArgumentParser(description="Run CAD extraction with langextract")
    parser.add_argument("--input", "-i", required=True, help="Input text file")
    parser.add_argument("--output", "-o", required=True, help="Output JSONL file")
    parser.add_argument("--html", help="Output HTML visualization file")
    parser.add_argument("--model", "-m", default="gemini-2.0-flash",
                        help="Model to use (default: gemini-2.0-flash)")
    parser.add_argument("--batch", "-b", action="store_true",
                        help="Use batch mode (slower, cheaper)")
    parser.add_argument("--mock", action="store_true",
                        help="Run in mock mode without langextract")
    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent.parent
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = script_dir / input_path

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = script_dir / output_path
    output_path.parent.mkdir(exist_ok=True)

    html_path = Path(args.html) if args.html else output_path.with_suffix('.html')
    if not html_path.is_absolute():
        html_path = script_dir / html_path
    html_path.parent.mkdir(exist_ok=True)

    # Check input exists
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        return 1

    # Check API key
    if not GOOGLE_API_KEY and not args.mock:
        print("ERROR: GOOGLE_API_KEY not set")
        print("Set it in .env file or environment variable")
        return 1

    # Load examples
    examples_path = script_dir / "config" / "examples.json"
    examples = load_examples(examples_path)

    print("=" * 60)
    print("CAD EXTRACTION")
    print("=" * 60)
    print(f"  Input: {input_path.name}")
    print(f"  Output: {output_path.name}")
    print(f"  HTML: {html_path.name}")
    print()

    start_time = datetime.now()

    # Run extraction
    if args.mock or not check_langextract():
        entry_count = run_extraction_mock(input_path, output_path, html_path, args.model)
    else:
        entry_count = run_extraction_real(input_path, output_path, html_path,
                                          args.model, examples, args.batch)

    elapsed = datetime.now() - start_time

    print()
    print("=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"  Entries extracted: {entry_count}")
    print(f"  Time elapsed: {elapsed}")
    print(f"  Output: {output_path}")
    print(f"  HTML: {html_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
