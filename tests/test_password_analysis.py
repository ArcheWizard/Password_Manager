import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_password_manager.utils.password_analysis import (
    calculate_entropy,
    check_common_patterns,
    evaluate_password_strength,
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
