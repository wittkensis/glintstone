#!/usr/bin/env python3
"""
Test lexical API functions with sample queries.

Verifies:
- Basic lookups (lemmas by form, senses, signs)
- Full chain retrieval (sign → lemmas → senses)
- Token integration
- Search functions
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.lexical import (
    lookup_lemmas_by_form,
    get_lemma_senses,
    get_signs_for_lemma,
    get_lemmas_for_sign,
    get_sign_full_chain,
    get_lemma_full_chain,
    get_token_lexical_context,
    search_lemmas,
    search_signs,
)


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")


def test_lookup_lemmas_by_form():
    """Test looking up lemmas by citation form."""
    print_section("TEST 1: Lookup Lemmas by Form")

    # Test Sumerian word
    print("Query: lugal (Sumerian)")
    lemmas = lookup_lemmas_by_form("lugal", language="sux")

    if lemmas:
        for lemma in lemmas:
            print(f"  • {lemma['citation_form']}[{lemma['guide_word']}]{lemma['pos']}")
            print(f"    Source: {lemma['source']}")
            print(f"    Senses: {lemma['sense_count']}, Signs: {lemma['sign_count']}")
            print(f"    Attestations: {lemma['attestation_count']}")
    else:
        print("  ⚠ No lemmas found")

    # Test Akkadian word
    print("\nQuery: šarru (Akkadian)")
    lemmas = lookup_lemmas_by_form("šarru", language="akk")

    if lemmas:
        for lemma in lemmas:
            print(f"  • {lemma['citation_form']}[{lemma['guide_word']}]{lemma['pos']}")
            print(f"    Source: {lemma['source']}, Dialect: {lemma['dialect']}")
            print(f"    Senses: {lemma['sense_count']}")
    else:
        print("  ⚠ No lemmas found")


def test_get_lemma_senses():
    """Test retrieving senses for a lemma."""
    print_section("TEST 2: Get Senses for Lemma")

    # Find a lemma first
    lemmas = lookup_lemmas_by_form("lugal", language="sux")

    if lemmas:
        lemma = lemmas[0]
        print(f"Lemma: {lemma['citation_form']}[{lemma['guide_word']}]{lemma['pos']}")

        senses = get_lemma_senses(lemma["id"])

        if senses:
            print(f"\nFound {len(senses)} sense(s):")
            for sense in senses:
                print(f"\n  Sense {sense['sense_number']}:")
                print(f"    Definition: {', '.join(sense['definition_parts'])}")
                if sense["usage_notes"]:
                    print(f"    Usage: {sense['usage_notes']}")
                print(f"    Source: {sense['source']}")
        else:
            print("  ⚠ No senses found")
    else:
        print("  ⚠ No lemma found to test")


def test_get_signs_for_lemma():
    """Test finding signs that can write a lemma."""
    print_section("TEST 3: Get Signs for Lemma")

    # Find a lemma first
    lemmas = lookup_lemmas_by_form("lugal", language="sux")

    if lemmas:
        lemma = lemmas[0]
        print(f"Lemma: {lemma['citation_form']}[{lemma['guide_word']}]{lemma['pos']}")

        signs = get_signs_for_lemma(lemma["id"])

        if signs:
            print(f"\nFound {len(signs)} sign(s) that can write this lemma:")
            for sign in signs:
                print(f"\n  Sign: {sign['sign_name']}")
                print(f"    Value: {sign['value']}")
                print(f"    Reading type: {sign['reading_type']}")
                print(f"    All values: {', '.join(sign['values'][:5])}...")
        else:
            print("  ⚠ No signs found")
    else:
        print("  ⚠ No lemma found to test")


def test_get_lemmas_for_sign():
    """Test finding lemmas that a sign can represent."""
    print_section("TEST 4: Get Lemmas for Sign")

    # Search for a sign first
    signs = search_signs("LUGAL")

    if signs:
        sign = signs[0]
        print(f"Sign: {sign['sign_name']}")
        print(f"Values: {', '.join(sign['values'][:10])}...")

        lemmas = get_lemmas_for_sign(sign["id"])

        if lemmas:
            print(f"\nFound {len(lemmas)} lemma(s) this sign can represent:")
            for lemma in lemmas[:5]:  # Show first 5
                print(
                    f"\n  {lemma['citation_form']}[{lemma['guide_word']}]{lemma['pos']}"
                )
                print(f"    Value: {lemma['value']}")
                print(f"    Reading type: {lemma['reading_type']}")
        else:
            print("  ⚠ No lemmas found")
    else:
        print("  ⚠ No sign found to test")


def test_get_sign_full_chain():
    """Test full chain retrieval for a sign."""
    print_section("TEST 5: Get Sign Full Chain")

    # Search for a sign first
    signs = search_signs("LUGAL")

    if signs:
        sign_id = signs[0]["id"]
        result = get_sign_full_chain(sign_id)

        if result:
            print(f"Sign: {result['sign']['sign_name']}")
            print(f"Source: {result['sign']['source']}")
            print(f"Values: {', '.join(result['sign']['values'][:10])}...")

            print(f"\nLemmas ({len(result['lemmas'])}):")
            for lemma_data in result["lemmas"][:3]:  # Show first 3
                print(
                    f"\n  {lemma_data['citation_form']}[{lemma_data['guide_word']}]{lemma_data['pos']}"
                )
                print(f"    Value: {lemma_data['value']}")
                print(f"    Reading type: {lemma_data['reading_type']}")

                if lemma_data["senses"]:
                    print(f"    Senses: {len(lemma_data['senses'])}")
                    for sense in lemma_data["senses"][:2]:  # Show first 2
                        print(f"      - {', '.join(sense['definition_parts'])}")

            if result["tablets"]:
                print(f"\nTablets: {len(result['tablets'])} (showing first 5)")
                for tablet in result["tablets"][:5]:
                    print(
                        f"  {tablet['p_number']}: {tablet['occurrence_count']} occurrence(s)"
                    )

            print(f"\nTotal occurrences: {result['total_occurrences']}")
        else:
            print("  ⚠ No result")
    else:
        print("  ⚠ No sign found to test")


def test_get_lemma_full_chain():
    """Test full chain retrieval for a lemma."""
    print_section("TEST 6: Get Lemma Full Chain")

    # Find a lemma first
    lemmas = lookup_lemmas_by_form("lugal", language="sux")

    if lemmas:
        lemma_id = lemmas[0]["id"]
        result = get_lemma_full_chain(lemma_id)

        if result:
            lemma = result["lemma"]
            print(
                f"Lemma: {lemma['citation_form']}[{lemma['guide_word']}]{lemma['pos']}"
            )
            print(f"Source: {lemma['source']}")
            print(f"Language: {lemma['language_code']}")

            print(f"\nSenses ({len(result['senses'])}):")
            for sense in result["senses"][:3]:  # Show first 3
                print(f"\n  Sense {sense['sense_number']}:")
                print(f"    {', '.join(sense['definition_parts'])}")

            print(f"\nSigns ({len(result['signs'])}):")
            for sign in result["signs"][:3]:  # Show first 3
                print(
                    f"  {sign['sign_name']} ({sign['value']}) - {sign['reading_type']}"
                )

            if result["tablets"]:
                print(f"\nTablets: {len(result['tablets'])} (showing first 5)")
                for tablet in result["tablets"][:5]:
                    print(
                        f"  {tablet['p_number']}: {tablet['occurrence_count']} occurrence(s)"
                    )

            print(f"\nTotal occurrences: {result['total_occurrences']}")
        else:
            print("  ⚠ No result")
    else:
        print("  ⚠ No lemma found to test")


def test_get_token_lexical_context():
    """Test token integration - getting lexical context for a token."""
    print_section("TEST 7: Get Token Lexical Context")

    # Test with common Sumerian word
    print("Token: lugal (Sumerian)")
    result = get_token_lexical_context("lugal", language="sux")

    print(f"Form: {result['token_form']}")
    print(f"Language: {result['language']}")
    print(f"Matching lemmas: {result['count']}")

    if result["lemmas"]:
        for lemma in result["lemmas"][:2]:  # Show first 2
            print(f"\n  {lemma['citation_form']}[{lemma['guide_word']}]{lemma['pos']}")
            print(f"    Source: {lemma['source']}")

            if lemma["senses"]:
                print(f"    Senses: {len(lemma['senses'])}")
                for sense in lemma["senses"][:2]:
                    print(f"      - {', '.join(sense['definition_parts'])}")

            if lemma["signs"]:
                print(f"    Signs: {len(lemma['signs'])}")
                for sign in lemma["signs"][:2]:
                    print(f"      - {sign['sign_name']} ({sign['value']})")
    else:
        print("  ⚠ No matching lemmas")


def test_search_lemmas():
    """Test lemma search."""
    print_section("TEST 8: Search Lemmas")

    # Test general search
    print("Query: king")
    results = search_lemmas("king", limit=5)

    if results:
        print(f"Found {len(results)} result(s):")
        for lemma in results:
            print(f"\n  {lemma['citation_form']}[{lemma['guide_word']}]{lemma['pos']}")
            print(f"    Language: {lemma['language_code']}, Source: {lemma['source']}")
            print(f"    Senses: {lemma['sense_count']}, Signs: {lemma['sign_count']}")
    else:
        print("  ⚠ No results")

    # Test language-filtered search
    print("\nQuery: king (Sumerian only)")
    results = search_lemmas("king", language="sux", limit=5)

    if results:
        print(f"Found {len(results)} result(s):")
        for lemma in results:
            print(f"  • {lemma['citation_form']}[{lemma['guide_word']}]{lemma['pos']}")
    else:
        print("  ⚠ No results")


def test_search_signs():
    """Test sign search."""
    print_section("TEST 9: Search Signs")

    # Search by sign name
    print("Query: DU")
    results = search_signs("DU", limit=5)

    if results:
        print(f"Found {len(results)} result(s):")
        for sign in results:
            print(f"\n  Sign: {sign['sign_name']}")
            print(f"    Values: {', '.join(sign['values'][:10])}...")
            print(f"    Lemmas: {sign['lemma_count']}")
    else:
        print("  ⚠ No results")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("LEXICAL API TEST SUITE")
    print("=" * 80)

    try:
        test_lookup_lemmas_by_form()
        test_get_lemma_senses()
        test_get_signs_for_lemma()
        test_get_lemmas_for_sign()
        test_get_sign_full_chain()
        test_get_lemma_full_chain()
        test_get_token_lexical_context()
        test_search_lemmas()
        test_search_signs()

        print("\n" + "=" * 80)
        print("✓ ALL TESTS COMPLETED")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
