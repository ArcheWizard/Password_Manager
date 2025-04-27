"""Backup and restore utilities."""
import json
import os
import time
from typing import List, Dict, Any, Optional
import sqlite3
import zipfile
import shutil

from utils.crypto import encrypt_password, decrypt_password
from utils.database import DB_FILE, get_passwords, add_password, get_categories, add_category
from utils.logger import log_info, log_error

def export_passwords(filename: str, master_password: str, include_notes: bool = True) -> bool:
    """Export passwords to an encrypted JSON file."""
    passwords = get_passwords()
    if not passwords:
        return False
    
    export_data = {
        "metadata": {
            "version": "2.0",
            "exported_at": int(time.time()),
            "entry_count": len(passwords)
        },
        "entries": []
    }
    
    for entry in passwords:
        # Map column indices to names for clarity
        entry_id, website, username, encrypted, category, notes, created_at, updated_at, expiry, favorite = entry
        
        password = decrypt_password(encrypted)
        entry_data = {
            "website": website,
            "username": username,
            "password": password,
            "category": category,
            "created_at": created_at,
            "updated_at": updated_at,
            "favorite": bool(favorite)
        }
        
        if include_notes:
            entry_data["notes"] = notes
            
        if expiry:
            entry_data["expiry_date"] = expiry
            
        export_data["entries"].append(entry_data)
    
    # Export categories as well
    categories = get_categories()
    export_data["categories"] = [{"name": name, "color": color} for name, color in categories]
    
    # Encrypt the entire JSON with the master password
    json_data = json.dumps(export_data)
    encrypted_data = encrypt_password(json_data, master_password)
    
    with open(filename, 'wb') as f:
        f.write(encrypted_data)
    
    # Log the export
    log_info(f"Exported {len(passwords)} passwords to {filename}")
    
    return True

def import_passwords(filename: str, master_password: str) -> int:
    """Import passwords from an encrypted JSON file. Returns count of imported items."""
    import time
    import json
    import sqlite3
    from utils.crypto import decrypt_password, encrypt_password
    from utils.database import add_password, add_category
    from utils.logger import log_info, log_error
    
    if not os.path.exists(filename):
        log_error(f"Import failed: File {filename} not found")
        return 0
    
    try:
        with open(filename, 'rb') as f:
            encrypted_data = f.read()
        
        try:
            json_data = decrypt_password(encrypted_data, master_password)
            import_data = json.loads(json_data)
        except Exception as e:
            log_error(f"Decryption error: {e}")
            return 0
        
        # Check for expected format
        if "entries" not in import_data:
            # Try legacy format
            if isinstance(import_data, list):
                entries = import_data
                version = "1.0"  # Legacy version
            else:
                raise ValueError("Invalid backup format")
        else:
            entries = import_data["entries"]
            version = import_data.get("metadata", {}).get("version", "1.0")
        
        # Import categories first if present
        if "categories" in import_data:
            for category in import_data["categories"]:
                try:
                    add_category(category["name"], category["color"])
                except Exception:
                    # Category already exists, skip
                    pass
        
        # Add each password individually to avoid transaction locks
        count = 0
        for item in entries:
            try:
                website = item["website"]
                username = item["username"]
                password = item["password"]
                
                # Get optional fields with defaults
                category = item.get("category", "General")
                notes = item.get("notes", "")
                expiry_days = None
                
                if "expiry_date" in item and item["expiry_date"]:
                    # Convert from timestamp to days from now
                    days_diff = (item["expiry_date"] - int(time.time())) / 86400
                    if days_diff > 0:
                        expiry_days = int(days_diff)
                
                # Use the add_password function directly
                encrypted = encrypt_password(password)
                add_password(website, username, encrypted, category, notes, expiry_days)
                count += 1
                
                # Add a small delay between operations to avoid locking
                time.sleep(0.05)
            except Exception as e:
                log_error(f"Failed to import item: {e}")
                # Continue with next item
        
        log_info(f"Imported {count} passwords from {filename} (format v{version})")
        return count
            
    except Exception as e:
        log_error(f"Import error: {e}")
        return 0

def create_full_backup(backup_dir: str, master_password: str) -> Optional[str]:
    """
    Create a complete backup including database, keys, and config.
    
    Returns:
        Path to the backup zip file or None if failed
    """
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = int(time.time())
    backup_filename = f"password_manager_backup_{timestamp}.zip"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Export passwords to a temporary file
        temp_export = os.path.join(backup_dir, "passwords_export.dat")
        export_passwords(temp_export, master_password)
        
        # Create the backup zip
        with zipfile.ZipFile(backup_path, 'w') as backup_zip:
            # Add the encrypted export
            backup_zip.write(temp_export, "passwords_export.dat")
            
            # Add the database file if it exists
            if os.path.exists("passwords.db"):
                backup_zip.write("passwords.db", "passwords.db")
            
            # Add the key file if it exists
            if os.path.exists("secret.key"):
                backup_zip.write("secret.key", "secret.key")
            
            # Add other config files
            if os.path.exists("auth.json"):
                backup_zip.write("auth.json", "auth.json")
                
            if os.path.exists("crypto.salt"):
                backup_zip.write("crypto.salt", "crypto.salt")
            
            # Add a metadata file
            metadata = {
                "version": "2.0",
                "timestamp": timestamp,
                "description": "Full password manager backup"
            }
            
            with open(os.path.join(backup_dir, "metadata.json"), 'w') as meta_file:
                json.dump(metadata, meta_file)
            
            backup_zip.write(os.path.join(backup_dir, "metadata.json"), "metadata.json")
        
        # Clean up temporary files
        os.remove(temp_export)
        os.remove(os.path.join(backup_dir, "metadata.json"))
        
        log_info(f"Created full backup at {backup_path}")
        return backup_path
        
    except Exception as e:
        log_error(f"Full backup failed: {e}")
        return None

def restore_from_backup(backup_path: str, master_password: str) -> bool:
    """
    Restore from a full backup.
    
    Returns:
        True if restoration was successful
    """
    if not os.path.exists(backup_path):
        log_error(f"Restore failed: Backup file {backup_path} not found")
        return False
        
    try:
        # Create a temporary directory for extraction
        temp_dir = os.path.join(os.path.dirname(backup_path), "temp_restore")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        # Extract the backup
        with zipfile.ZipFile(backup_path, 'r') as backup_zip:
            backup_zip.extractall(temp_dir)
        
        # Check if this is a valid backup
        if not os.path.exists(os.path.join(temp_dir, "passwords_export.dat")):
            log_error("Invalid backup: missing passwords export")
            shutil.rmtree(temp_dir)
            return False
        
        # Create backups of current files
        backup_suffix = int(time.time())
        if os.path.exists("passwords.db"):
            shutil.copy("passwords.db", f"passwords.db.bak{backup_suffix}")
            
        if os.path.exists("secret.key"):
            shutil.copy("secret.key", f"secret.key.bak{backup_suffix}")
            
        if os.path.exists("auth.json"):
            shutil.copy("auth.json", f"auth.json.bak{backup_suffix}")
            
        if os.path.exists("crypto.salt"):
            shutil.copy("crypto.salt", f"crypto.salt.bak{backup_suffix}")
        
        # Restore files
        for filename in ["passwords.db", "secret.key", "auth.json", "crypto.salt"]:
            source_path = os.path.join(temp_dir, filename)
            if os.path.exists(source_path):
                shutil.copy(source_path, filename)
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        log_info(f"Successfully restored from backup {backup_path}")
        return True
        
    except Exception as e:
        log_error(f"Restore failed: {e}")
        return False