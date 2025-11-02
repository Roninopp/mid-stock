"""
User Approval System
Manages approved users for the bot
"""

import json
import os
from logs import logger
import config

APPROVED_USERS_FILE = "approved_users.json"

def load_approved_users():
    """Load approved users from file"""
    try:
        if os.path.exists(APPROVED_USERS_FILE):
            with open(APPROVED_USERS_FILE, 'r') as f:
                data = json.load(f)
                return set(data.get('users', []))
        else:
            # Initialize with admin
            return {config.ADMIN_USER_ID}
    except Exception as e:
        logger.error(f"Error loading approved users: {str(e)}")
        return {config.ADMIN_USER_ID}

def save_approved_users(users):
    """Save approved users to file"""
    try:
        with open(APPROVED_USERS_FILE, 'w') as f:
            json.dump({'users': list(users)}, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving approved users: {str(e)}")
        return False

def is_user_approved(user_id):
    """Check if user is approved"""
    approved_users = load_approved_users()
    return user_id in approved_users

def add_user(user_id):
    """Add user to approved list"""
    approved_users = load_approved_users()
    
    if user_id in approved_users:
        return False  # Already approved
    
    approved_users.add(user_id)
    save_approved_users(approved_users)
    logger.info(f"✅ User {user_id} approved")
    return True

def remove_user(user_id):
    """Remove user from approved list"""
    if user_id == config.ADMIN_USER_ID:
        logger.warning("Cannot remove admin user")
        return False
    
    approved_users = load_approved_users()
    
    if user_id not in approved_users:
        return False
    
    approved_users.remove(user_id)
    save_approved_users(approved_users)
    logger.info(f"❌ User {user_id} removed")
    return True

def get_approved_users():
    """Get list of all approved users"""
    return list(load_approved_users())
