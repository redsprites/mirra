#!/usr/bin/env python3
"""
Instagram Saved Videos Downloader
A simple script to download saved videos from your Instagram account.
"""

import os
import sys
import argparse
import getpass
import instaloader
from pathlib import Path
from dotenv import load_dotenv


class InstagramSavedVideos:
    def __init__(self, username, password):
        """
        Initialize the Instagram connection.
        
        Args:
            username (str): Your Instagram username
            password (str): Your Instagram password
        """
        self.username = username
        self.password = password
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
        )
        
    def login(self):
        """Login to Instagram."""
        # Try to load existing session first
        try:
            self.loader.load_session_from_file(self.username)
            print(f"✓ Loaded existing session for {self.username}")
            print(f"Verifying session...")
            # Test if session is valid
            profile = instaloader.Profile.from_username(self.loader.context, self.username)
            print("✓ Session is valid!")
            return True
        except:
            # Session doesn't exist or is invalid, proceed with login
            pass
        
        try:
            print(f"Logging in as {self.username}...")
            self.loader.login(self.username, self.password)
            print("✓ Successfully logged in!")
            # Save session for future use
            self.loader.save_session_to_file()
            print("✓ Session saved for future use!")
            return True
        except instaloader.exceptions.BadCredentialsException:
            print("✗ Error: Invalid username or password")
            return False
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            print("\n" + "="*50)
            print("Two-factor authentication required!")
            print("="*50)
            print("Check for your 2FA code in:")
            print("  • SMS/Text message on your phone")
            print("  • Authenticator app (Google Authenticator, Authy, etc.)")
            print("  • Email (if set up as backup)")
            print("="*50)
            code = input("\nEnter 2FA code: ").strip()
            try:
                self.loader.two_factor_login(code)
                print("✓ Successfully logged in with 2FA!")
                # Save session for future use
                self.loader.save_session_to_file()
                print("✓ Session saved for future use!")
                return True
            except Exception as e:
                print(f"\n✗ 2FA Error: {e}")
                print("\nTroubleshooting tips:")
                print("  • Make sure you entered the code correctly (6 digits)")
                print("  • The code might have expired - request a new one")
                print("  • Try logging into Instagram via browser first")
                print("  • Instagram may be blocking automated access temporarily")
                print("  • Wait a few minutes and try again")
                return False
        except Exception as e:
            print(f"✗ Login error: {e}")
            return False
    
    def get_saved_videos(self, output_dir="saved_videos", limit=None):
        """
        Download saved videos from Instagram.
        
        Args:
            output_dir (str): Directory to save videos
            limit (int): Maximum number of videos to download (None for all)
        """
        try:
            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            print(f"\nFetching saved posts...")
            profile = instaloader.Profile.from_username(
                self.loader.context, 
                self.username
            )
            
            saved_posts = profile.get_saved_posts()
            
            video_count = 0
            total_count = 0
            
            for post in saved_posts:
                total_count += 1
                
                # Check if we've reached the limit
                if limit and video_count >= limit:
                    print(f"\nReached limit of {limit} videos.")
                    break
                
                # Only process video posts
                if post.is_video:
                    try:
                        video_count += 1
                        print(f"\n[{video_count}] Downloading video from @{post.owner_username}...")
                        print(f"    Post URL: https://www.instagram.com/p/{post.shortcode}/")
                        
                        # Create a folder for this video
                        video_folder_name = f"{post.date_utc.strftime('%Y-%m-%d_%H-%M-%S')}_UTC_{post.shortcode}"
                        video_folder = Path(output_dir) / video_folder_name
                        video_folder.mkdir(parents=True, exist_ok=True)
                        
                        # Temporarily change to output directory and download
                        original_cwd = os.getcwd()
                        try:
                            os.chdir(output_dir)
                            # Download with just the folder name as target
                            self.loader.download_post(post, target=video_folder_name)
                        finally:
                            os.chdir(original_cwd)
                        
                        print(f"    ✓ Downloaded to: {video_folder_name}/")
                        
                    except Exception as e:
                        print(f"    ✗ Error downloading video: {e}")
                else:
                    print(f"Skipping non-video post {total_count}...", end='\r')
            
            print(f"\n\n{'='*50}")
            print(f"Summary:")
            print(f"  Total saved posts checked: {total_count}")
            print(f"  Videos downloaded: {video_count}")
            print(f"  Output directory: {os.path.abspath(output_dir)}")
            print(f"{'='*50}")
            
        except instaloader.exceptions.LoginRequiredException:
            print("✗ Error: Login required. Please check your credentials.")
        except Exception as e:
            print(f"✗ Error fetching saved videos: {e}")


def main():
    """Main function to run the script."""
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description='Download saved videos from your Instagram account'
    )
    parser.add_argument(
        '-u', '--username',
        help='Instagram username (will prompt if not provided)'
    )
    parser.add_argument(
        '-p', '--password',
        help='Instagram password (will prompt if not provided)'
    )
    parser.add_argument(
        '-l', '--limit',
        type=int,
        help='Maximum number of videos to download (default: all)'
    )
    parser.add_argument(
        '-o', '--output',
        default='saved_videos',
        help='Output directory (default: saved_videos)'
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("Instagram Saved Videos Downloader")
    print("=" * 50)
    
    # Get credentials (priority: CLI args > .env file > prompt)
    if args.username:
        username = args.username
    elif os.getenv('INSTAGRAM_USERNAME'):
        username = os.getenv('INSTAGRAM_USERNAME')
        print(f"\n✓ Using username from .env file")
    else:
        username = input("\nEnter your Instagram username: ").strip()
    
    # Remove @ symbol if present
    username = username.lstrip('@')
    
    print(f"Username: {username}")
    
    if args.password:
        password = args.password
    elif os.getenv('INSTAGRAM_PASSWORD'):
        password = os.getenv('INSTAGRAM_PASSWORD')
        print("✓ Using password from .env file")
    else:
        password = getpass.getpass("Enter your Instagram password: ")
    
    if not username or not password:
        print("✗ Error: Username and password are required.")
        return
    
    # Optional: limit number of videos
    limit = args.limit
    if limit is None and os.getenv('INSTAGRAM_LIMIT'):
        limit = int(os.getenv('INSTAGRAM_LIMIT'))
        print(f"✓ Using limit from .env file: {limit}")
    elif limit is None and sys.stdin.isatty():
        limit_input = input("Enter max number of videos to download (press Enter for all): ").strip()
        limit = int(limit_input) if limit_input.isdigit() else None
    
    # Create instance and login
    ig = InstagramSavedVideos(username, password)
    
    if ig.login():
        # Download saved videos
        ig.get_saved_videos(output_dir=args.output, limit=limit)
    else:
        print("\n✗ Failed to login. Please try again.")


if __name__ == "__main__":
    main()


