"""Backup and restore utilities."""
import json
import os
from typing import List, Dict, Any

from utils.crypto import encrypt_password, decrypt_password
from utils.database import get_passwords, add_password

def export_passwords(filename: str, master_password: str) -> bool:
    """Export passwords to an encrypted JSON file."""
    passwords = get_passwords()
    if not passwords:
        return False
    
    export_data = []
    for entry_id, website, username, encrypted in passwords:
        password = decrypt_password(encrypted)
        export_data.append({
            "website": website,
            "username": username,
            "password": password
        })
    
    # Encrypt the entire JSON with the master password
    json_data = json.dumps(export_data)
    encrypted_data = encrypt_password(json_data)
    
    with open(filename, 'wb') as f:
        f.write(encrypted_data)
    
    return True

def import_passwords(filename: str, master_password: str) -> int:
    """Import passwords from an encrypted JSON file. Returns count of imported items."""
    if not os.path.exists(filename):
        return 0
    
    try:
        with open(filename, 'rb') as f:
            encrypted_data = f.read()
        
        json_data = decrypt_password(encrypted_data)
        import_data = json.loads(json_data)
        
        count = 0
        for item in import_data:
            website = item["website"]
            username = item["username"]
            password = item["password"]
            
            encrypted = encrypt_password(password)
            add_password(website, username, encrypted)
            count += 1
        
        return count
    except Exception as e:
        print(f"Import error: {e}")
        return 0