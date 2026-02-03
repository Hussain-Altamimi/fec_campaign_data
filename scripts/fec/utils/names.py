"""Name capitalization utilities for FEC data."""

import re

# Suffixes to preserve in title case
SUFFIXES = {"JR", "SR", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"}

# Common lowercase particles in names (only lowercase when not first word)
LOWERCASE_PARTICLES = {"DE", "LA", "DEL", "VAN", "VON", "DEN", "DER", "LE", "DA", "DI", "DU", "OF", "THE"}

# Common acronyms/abbreviations to preserve uppercase (for organization names)
ACRONYMS = {
    "AFL-CIO", "AFL", "CIO", "PAC", "USA", "US", "IBEW", "UAW", "SEIU", "NEA",
    "AFT", "UFCW", "AFSCME", "LIUNA", "IATSE", "IUOE", "SMART", "UWUA", "CWA",
    "APWU", "NALC", "NFFE", "NTEU", "PBA", "FOP", "IAFF", "BCTGM", "USW",
    "OPEIU", "UFWA", "DNC", "RNC", "GOP", "LLC", "INC", "LTD", "CO", "CORP",
}

# Abbreviations to capitalize specially
ABBREVIATIONS = {"INT'L": "Int'l", "INTL": "Intl", "ASS'N": "Ass'n", "ASSN": "Assn"}


def capitalize_name(name: str | None) -> str | None:
    """Convert ALL-CAPS name to Capital Case.

    Handles special cases:
    - Suffixes: JR, SR, II, III, IV (title case: Jr, Sr)
    - Irish/Scottish prefixes: O'BRIEN -> O'Brien, MCDONALD -> McDonald
    - Nicknames in quotes: "PAT" -> "Pat"
    - Parenthetical nicknames: (KIKA) -> (Kika)
    - Lowercase particles: DE LA, VAN, VON (lowercase except when first)

    Args:
        name: ALL-CAPS name string (e.g., "SMITH, JOHN JR")

    Returns:
        Capital Case name (e.g., "Smith, John Jr"), or None if input is None/empty
    """
    if name is None:
        return None

    if not isinstance(name, str):
        return name

    name = name.strip()
    if not name:
        return name

    # Handle "LAST, FIRST" format (common for candidate names)
    if "," in name:
        parts = name.split(",", 1)
        last = _capitalize_part(parts[0].strip(), is_first_part=True)
        first = _capitalize_part(parts[1].strip(), is_first_part=False) if len(parts) > 1 else ""
        return f"{last}, {first}".rstrip(", ")

    # Single name or organization name
    return _capitalize_part(name, is_first_part=True)


def _capitalize_part(text: str, is_first_part: bool) -> str:
    """Capitalize a part of a name (either last name or first name portion)."""
    if not text:
        return text

    # Handle quoted nicknames: ""PAT"" or "PAT"
    text = re.sub(
        r'""([^"]+)""',
        lambda m: f'""{ _capitalize_word(m.group(1), is_first=True)}""',
        text,
    )
    text = re.sub(
        r'"([^"]+)"',
        lambda m: f'"{_capitalize_word(m.group(1), is_first=True)}"',
        text,
    )

    # Handle parenthetical nicknames: (PAT) or (KIKA)
    text = re.sub(
        r"\(([^)]+)\)",
        lambda m: f"({_capitalize_word(m.group(1), is_first=True)})",
        text,
    )

    # Split into words and capitalize each
    words = text.split()
    result = []

    for i, word in enumerate(words):
        is_first = is_first_part and i == 0
        capitalized = _capitalize_word(word, is_first=is_first)
        result.append(capitalized)

    return " ".join(result)


def _capitalize_word(word: str, is_first: bool = False) -> str:
    """Capitalize a single word with special handling.

    Args:
        word: The word to capitalize
        is_first: Whether this is the first word in the name

    Returns:
        Capitalized word
    """
    if not word:
        return word

    # Preserve any leading/trailing punctuation
    leading = ""
    trailing = ""

    # Extract leading punctuation
    i = 0
    while i < len(word) and not word[i].isalnum():
        leading += word[i]
        i += 1

    # Extract trailing punctuation
    j = len(word) - 1
    while j >= i and not word[j].isalnum():
        trailing = word[j] + trailing
        j -= 1

    # Get the core word without punctuation
    core = word[i : j + 1] if i <= j else ""

    if not core:
        return word

    upper_core = core.upper()

    # Check for abbreviations with special capitalization (Int'l, Ass'n, etc.)
    if upper_core in ABBREVIATIONS:
        return leading + ABBREVIATIONS[upper_core] + trailing

    # Check for acronyms (AFL-CIO, PAC, USA, etc.)
    if upper_core in ACRONYMS:
        return leading + upper_core + trailing

    # Check for suffixes (Jr, Sr, II, III, etc.)
    # Roman numerals stay uppercase, Jr/Sr become title case
    if upper_core in SUFFIXES:
        if upper_core in {"JR", "SR"}:
            return leading + core.title() + trailing
        else:
            # Roman numerals stay uppercase
            return leading + upper_core + trailing

    # Check for lowercase particles (de, la, van, von, etc.)
    # Only lowercase if not the first word
    if not is_first and upper_core in LOWERCASE_PARTICLES:
        return leading + core.lower() + trailing

    # Handle Irish O' prefix: O'BRIEN -> O'Brien
    if upper_core.startswith("O'") and len(core) > 2:
        return leading + "O'" + core[2:].title() + trailing

    # Handle Scottish Mc prefix: MCDONALD -> McDonald
    if upper_core.startswith("MC") and len(core) > 2:
        return leading + "Mc" + core[2:].title() + trailing

    # Note: We intentionally don't handle "Mac" prefix (MACDONALD -> MacDonald)
    # because it's difficult to distinguish Scottish names from regular names
    # like MACKEY without a dictionary. Standard title case is safer.

    # Handle hyphenated words: SMITH-JONES -> Smith-Jones, but AFL-CIO -> AFL-CIO
    if "-" in core:
        # First check if the whole hyphenated word is a known acronym
        if upper_core in ACRONYMS:
            return leading + upper_core + trailing
        parts = core.split("-")
        capitalized_parts = [_capitalize_word(p, is_first=(is_first and i == 0)) for i, p in enumerate(parts)]
        return leading + "-".join(capitalized_parts) + trailing

    # Standard title case
    return leading + core.title() + trailing
