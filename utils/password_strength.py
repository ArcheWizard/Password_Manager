"""Password strength evaluation."""
import re
from typing import Tuple

def evaluate_password_strength(password: str) -> Tuple[int, str]:
    """
    Evaluate password strength on a scale of 0-5.
    
    Returns:
        Tuple containing (score, description)
    """
    score = 0
    feedback = []
    
    # Length check
    if len(password) < 8:
        feedback.append("Too short")
    elif len(password) >= 12:
        score += 1
        feedback.append("Good length")
    
    # Complexity checks
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("No uppercase letters")
    
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("No lowercase letters")
    
    if re.search(r'[0-9]', password):
        score += 1
    else:
        feedback.append("No numbers")
    
    if re.search(r'[^A-Za-z0-9]', password):
        score += 1
    else:
        feedback.append("No special characters")
    
    # Determine description based on score
    if score == 5:
        description = "Very Strong"
    elif score == 4:
        description = "Strong"
    elif score == 3:
        description = "Medium"
    elif score == 2:
        description = "Weak"
    else:
        description = "Very Weak"
    
    return score, description

def generate_secure_password(length: int = 16) -> str:
    """Generate a secure random password."""
    import random
    import string
    
    characters = string.ascii_lowercase + string.ascii_uppercase + string.digits + "!@#$%^&*()_-+=<>?"
    secure_password = ''.join(random.choice(characters) for _ in range(length))
    
    return secure_password