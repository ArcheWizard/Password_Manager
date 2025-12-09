"""Enhanced password generation with pattern-based and configurable options.

This module extends the basic password generation with advanced features like
pattern-based generation, pronounceable passwords, and customizable character sets.
"""

from __future__ import annotations

import random
import re
import string
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class PasswordStyle(Enum):
    """Password generation styles."""

    RANDOM = "random"  # Pure random characters
    MEMORABLE = "memorable"  # Easy to remember (word-based)
    PIN = "pin"  # Numbers only
    PASSPHRASE = "passphrase"  # Multiple words separated by delimiter
    PATTERN = "pattern"  # Custom pattern-based


@dataclass
class PasswordOptions:
    """Options for password generation."""

    length: int = 16
    include_uppercase: bool = True
    include_lowercase: bool = True
    include_digits: bool = True
    include_special: bool = True
    exclude_ambiguous: bool = False  # Exclude 0, O, l, 1, I, etc.
    exclude_similar: bool = False  # Exclude similar-looking characters
    custom_characters: Optional[str] = None  # Custom character set
    start_with_letter: bool = False  # Some systems require this
    no_repeating: bool = False  # No consecutive repeated characters
    min_uppercase: int = 1
    min_lowercase: int = 1
    min_digits: int = 1
    min_special: int = 0


# Consonants and vowels for pronounceable passwords
CONSONANTS = "bcdfghjklmnpqrstvwxyz"
VOWELS = "aeiou"

# Ambiguous characters that might be confused
AMBIGUOUS_CHARS = "0O1lI|"

# Similar looking characters
SIMILAR_CHARS = "il1Lo0O"

# Common word lists for passphrases (simplified)
WORD_LIST = [
    "alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel",
    "india", "juliet", "kilo", "lima", "mike", "november", "oscar", "papa",
    "quebec", "romeo", "sierra", "tango", "uniform", "victor", "whiskey",
    "xray", "yankee", "zulu", "correct", "horse", "battery", "staple",
    "mountain", "river", "ocean", "forest", "desert", "valley", "canyon",
    "meadow", "sunset", "sunrise", "thunder", "lightning", "rainbow", "crystal"
]


def _build_character_set(options: PasswordOptions) -> str:
    """Build character set based on options."""
    if options.custom_characters:
        return options.custom_characters

    chars = ""

    if options.include_lowercase:
        chars += string.ascii_lowercase

    if options.include_uppercase:
        chars += string.ascii_uppercase

    if options.include_digits:
        chars += string.digits

    if options.include_special:
        chars += "!@#$%^&*()_-+=<>?[]{}|:;,./"

    # Remove ambiguous characters if requested
    if options.exclude_ambiguous:
        chars = "".join(c for c in chars if c not in AMBIGUOUS_CHARS)

    # Remove similar characters if requested
    if options.exclude_similar:
        chars = "".join(c for c in chars if c not in SIMILAR_CHARS)

    return chars


def _meets_requirements(password: str, options: PasswordOptions) -> bool:
    """Check if password meets minimum requirements."""
    if options.include_uppercase and options.min_uppercase > 0:
        if sum(1 for c in password if c.isupper()) < options.min_uppercase:
            return False

    if options.include_lowercase and options.min_lowercase > 0:
        if sum(1 for c in password if c.islower()) < options.min_lowercase:
            return False

    if options.include_digits and options.min_digits > 0:
        if sum(1 for c in password if c.isdigit()) < options.min_digits:
            return False

    if options.include_special and options.min_special > 0:
        special_chars = "!@#$%^&*()_-+=<>?[]{}|:;,./"
        if sum(1 for c in password if c in special_chars) < options.min_special:
            return False

    # Check for repeating characters if not allowed
    if options.no_repeating:
        for i in range(len(password) - 1):
            if password[i] == password[i + 1]:
                return False

    # Check start with letter requirement
    if options.start_with_letter and not password[0].isalpha():
        return False

    return True


def generate_random_password(options: PasswordOptions) -> str:
    """Generate a random password with given options."""
    max_attempts = 1000

    for _ in range(max_attempts):
        chars = _build_character_set(options)
        if not chars:
            raise ValueError("No characters available for password generation")

        password = "".join(random.choice(chars) for _ in range(options.length))

        if _meets_requirements(password, options):
            return password

    raise ValueError(f"Could not generate password meeting requirements after {max_attempts} attempts")


def generate_memorable_password(length: int = 12) -> str:
    """Generate a memorable (pronounceable) password."""
    password = []

    # Alternate between consonants and vowels
    for i in range(length):
        if i % 2 == 0:
            password.append(random.choice(CONSONANTS))
        else:
            password.append(random.choice(VOWELS))

    result = "".join(password)

    # Capitalize some characters randomly
    result_chars = list(result)
    for i in random.sample(range(len(result_chars)), min(3, len(result_chars))):
        result_chars[i] = result_chars[i].upper()

    # Add a digit and special character
    if length > 4:
        result_chars[random.randrange(len(result_chars))] = str(random.randint(0, 9))
        result_chars[random.randrange(len(result_chars))] = random.choice("!@#$%^&*")

    return "".join(result_chars)


def generate_pin(length: int = 6) -> str:
    """Generate a numeric PIN."""
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def generate_passphrase(word_count: int = 4, separator: str = "-", capitalize: bool = True) -> str:
    """Generate a passphrase from random words."""
    words = random.sample(WORD_LIST, min(word_count, len(WORD_LIST)))

    if capitalize:
        words = [word.capitalize() for word in words]

    return separator.join(words)


def generate_pattern_password(pattern: str) -> str:
    """Generate password based on a pattern.

    Pattern syntax:
        l = lowercase letter
        u = uppercase letter
        d = digit
        s = special character
        a = any character
        [chars] = one of the specified characters
        {n} = repeat previous n times

    Examples:
        "ulllddss" = One uppercase, three lowercase, two digits, two special
        "l{8}d{4}" = 8 lowercase letters, 4 digits
        "[aeiou]{3}" = 3 random vowels
    """
    result = []
    i = 0

    while i < len(pattern):
        char = pattern[i]

        # Check for repetition {n}
        repeat = 1
        if i + 1 < len(pattern) and pattern[i + 1] == '{':
            end_brace = pattern.find('}', i + 2)
            if end_brace != -1:
                repeat = int(pattern[i + 2:end_brace])
                i = end_brace + 1
        else:
            i += 1

        # Generate character(s) based on pattern
        if char == 'l':
            result.extend(random.choice(string.ascii_lowercase) for _ in range(repeat))
        elif char == 'u':
            result.extend(random.choice(string.ascii_uppercase) for _ in range(repeat))
        elif char == 'd':
            result.extend(random.choice(string.digits) for _ in range(repeat))
        elif char == 's':
            result.extend(random.choice("!@#$%^&*()_-+=<>?") for _ in range(repeat))
        elif char == 'a':
            all_chars = string.ascii_letters + string.digits + "!@#$%^&*()_-+=<>?"
            result.extend(random.choice(all_chars) for _ in range(repeat))
        elif char == '[':
            # Custom character class
            end_bracket = pattern.find(']', i)
            if end_bracket != -1:
                custom_chars = pattern[i:end_bracket]
                result.extend(random.choice(custom_chars) for _ in range(repeat))
                i = end_bracket + 1

    return "".join(result)


def generate_password(
    style: PasswordStyle = PasswordStyle.RANDOM,
    options: Optional[PasswordOptions] = None,
    pattern: Optional[str] = None,
    word_count: int = 4,
    separator: str = "-",
) -> str:
    """Generate a password based on specified style and options.

    Args:
        style: Password generation style
        options: Options for random password generation
        pattern: Pattern string for pattern-based generation
        word_count: Number of words for passphrase
        separator: Separator for passphrase words

    Returns:
        Generated password string
    """
    if options is None:
        options = PasswordOptions()

    if style == PasswordStyle.RANDOM:
        return generate_random_password(options)
    elif style == PasswordStyle.MEMORABLE:
        return generate_memorable_password(options.length)
    elif style == PasswordStyle.PIN:
        return generate_pin(options.length)
    elif style == PasswordStyle.PASSPHRASE:
        return generate_passphrase(word_count, separator)
    elif style == PasswordStyle.PATTERN:
        if not pattern:
            raise ValueError("Pattern required for pattern-based generation")
        return generate_pattern_password(pattern)
    else:
        raise ValueError(f"Unknown password style: {style}")


def estimate_password_strength(password: str) -> dict:
    """Estimate the strength and time to crack a password."""
    from secure_password_manager.utils.password_analysis import (
        calculate_entropy,
        evaluate_password_strength,
    )

    score, strength = evaluate_password_strength(password)
    entropy = calculate_entropy(password)

    # Estimate time to crack at various speeds (guesses per second)
    # Modern GPU: 100 billion guesses/sec
    # Botnet: 1 trillion guesses/sec

    possible_combinations = 2 ** entropy

    # Time in seconds at 100 billion guesses/sec
    seconds = possible_combinations / 1e11

    # Convert to human-readable format
    if seconds < 60:
        time_estimate = f"{seconds:.1f} seconds"
    elif seconds < 3600:
        time_estimate = f"{seconds/60:.1f} minutes"
    elif seconds < 86400:
        time_estimate = f"{seconds/3600:.1f} hours"
    elif seconds < 31536000:
        time_estimate = f"{seconds/86400:.1f} days"
    else:
        years = seconds / 31536000
        if years > 1e6:
            time_estimate = f"{years/1e6:.1f} million years"
        elif years > 1e9:
            time_estimate = f"{years/1e9:.1f} billion years"
        else:
            time_estimate = f"{years:.1f} years"

    return {
        "score": score,
        "strength": strength,
        "entropy": entropy,
        "length": len(password),
        "crack_time": time_estimate,
    }
