#!/usr/bin/env python3
"""
Test Instagram login and save session
This script helps you establish a session with Instagram that can be reused.
"""

import instaloader
import sys
import getpass


def test_login():
    """Test login and save session."""
    print("Instagram Login Test")
    print("=" * 50)
    
    username = input("Enter your Instagram username (without @): ").strip().lstrip('@')
    password = getpass.getpass("Enter your Instagram password: ")
    
    # Create loader with session file
    loader = instaloader.Instaloader()
    
    print(f"\nAttempting to login as: {username}")
    
    try:
        loader.login(username, password)
        print("✓ Login successful!")
        
        # Save session for reuse
        loader.save_session_to_file()
        print(f"✓ Session saved! You can now use the main script.")
        print(f"  Session file: ~/.config/instaloader/session-{username}")
        
        return True
        
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        print("\n2FA Required - Check your phone/authenticator app")
        code = input("Enter 2FA code: ").strip()
        try:
            loader.two_factor_login(code)
            print("✓ Login successful with 2FA!")
            
            # Save session
            loader.save_session_to_file()
            print(f"✓ Session saved!")
            print(f"  Session file: ~/.config/instaloader/session-{username}")
            
            return True
        except Exception as e:
            print(f"✗ 2FA failed: {e}")
            print("\nPossible issues:")
            print("  • Instagram may be blocking automated access")
            print("  • Try waiting 10-15 minutes and try again")
            print("  • Make sure you can login via browser/app first")
            return False
            
    except instaloader.exceptions.BadCredentialsException:
        print("✗ Invalid username or password")
        return False
        
    except Exception as e:
        print(f"✗ Login error: {e}")
        print("\nInstagram may be blocking automated logins.")
        print("Try these steps:")
        print("  1. Login via Instagram app/website first")
        print("  2. Wait 10-15 minutes")
        print("  3. Try this script again")
        return False


if __name__ == "__main__":
    test_login()

