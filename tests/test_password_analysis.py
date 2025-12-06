import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.password_analysis import (
    calculate_entropy,
    check_common_patterns,
    evaluate_password_strength,
    generate_secure_password,
    get_password_improvement_suggestions,
)


def test_password_strength_evaluation():
    """Test password strength evaluation."""
    # Very weak password
    score, strength = evaluate_password_strength("password")
    assert score <= 2
    assert strength in ["Very Weak", "Weak"]

    # Medium password
    score, strength = evaluate_password_strength("Password123")
    assert score == 2
    assert strength == "Weak"

    # Strong password
    score, strength = evaluate_password_strength("P@ssw0rd123!")
    assert score >= 4
    assert strength in ["Strong", "Very Strong"]

    # Very strong password
    score, strength = evaluate_password_strength("uE4$x9Lm!2pQr&7Z")
    assert score == 5
    assert strength == "Very Strong"


def test_entropy_calculation():
    """Test password entropy calculation."""
    # Simple password with low entropy
    entropy = calculate_entropy("password")
    assert entropy < 50

    # Complex password with high entropy
    entropy = calculate_entropy("uE4$x9Lm!2pQr&7Z")
    assert entropy > 80


def test_common_pattern_detection():
    """Test detection of common patterns in passwords."""
    # Sequential numbers
    weaknesses = check_common_patterns("password123")
    assert "Contains sequential numbers" in weaknesses

    # Sequential letters
    weaknesses = check_common_patterns("passwordabc")
    assert "Contains sequential letters" in weaknesses

    # Repeated characters
    weaknesses = check_common_patterns("passwordaaa")
    assert "Contains repeated characters" in weaknesses

    # Keyboard pattern
    weaknesses = check_common_patterns("passwordqwe")
    assert "Contains keyboard pattern" in weaknesses

    # Strong password should have no patterns
    weaknesses = check_common_patterns("uE4$x9Lm!2pQr&7Z")
    assert not weaknesses


def test_improvement_suggestions():
    """Test password improvement suggestions."""
    # Weak password should have multiple suggestions
    suggestions = get_password_improvement_suggestions("password")
    assert len(suggestions) >= 3

    # Missing character classes
    suggestions = get_password_improvement_suggestions("password123")
    assert "Add uppercase letters" in suggestions
    assert "Add special characters" in suggestions

    # Too short
    suggestions = get_password_improvement_suggestions("Pw1!")
    assert "Make your password longer" in suggestions

    # Very strong password should have no or few suggestions
    suggestions = get_password_improvement_suggestions("uE4$x9Lm!2pQr&7Z")
    assert len(suggestions) <= 1


def test_generate_secure_password():
    """Test secure password generation."""
    # Default length with special characters
    password = generate_secure_password()
    assert len(password) == 16
    assert any(c.isupper() for c in password)
    assert any(c.islower() for c in password)
    assert any(c.isdigit() for c in password)
    assert any(c in "!@#$%^&*()_-+=<>?" for c in password)

    # Custom length without special characters
    password = generate_secure_password(length=20, include_special=False)
    assert len(password) == 20
    assert any(c.isupper() for c in password)
    assert any(c.islower() for c in password)
    assert any(c.isdigit() for c in password)
    assert not any(c in "!@#$%^&*()_-+=<>?" for c in password)

    # Short password
    password = generate_secure_password(length=8)
    assert len(password) == 8


def test_calculate_entropy_edge_cases():
    """Test entropy calculation edge cases."""
    # Empty password
    assert calculate_entropy("") == 0

    # Only lowercase
    entropy_lower = calculate_entropy("abcdefgh")
    assert 35 < entropy_lower < 45  # 8 * log2(26) ≈ 37.6

    # Only uppercase
    entropy_upper = calculate_entropy("ABCDEFGH")
    assert 35 < entropy_upper < 45

    # Only digits
    entropy_digits = calculate_entropy("12345678")
    assert 25 < entropy_digits < 30  # 8 * log2(10) ≈ 26.6

    # Mixed character classes
    entropy_mixed = calculate_entropy("Abc123!@")
    assert entropy_mixed > 50  # Higher due to larger character pool


def test_check_common_patterns_keyboard_sequences():
    """Test detection of keyboard patterns."""
    # QWERTY row
    weaknesses = check_common_patterns("passwordqwerty")
    assert any("keyboard pattern" in w.lower() for w in weaknesses)

    # ASDFGH row
    weaknesses = check_common_patterns("passwordasdfgh")
    assert any("keyboard pattern" in w.lower() for w in weaknesses)


def test_password_improvement_missing_characters():
    """Test suggestions for missing character types."""
    # Missing uppercase
    suggestions = get_password_improvement_suggestions("password123!")
    assert "Add uppercase letters" in suggestions

    # Missing lowercase
    suggestions = get_password_improvement_suggestions("PASSWORD123!")
    assert "Add lowercase letters" in suggestions

    # Missing numbers
    suggestions = get_password_improvement_suggestions("Password!@#")
    assert "Add numbers" in suggestions

    # Missing special characters
    suggestions = get_password_improvement_suggestions("Password123")
    assert "Add special characters" in suggestions
