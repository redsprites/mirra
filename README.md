# Instagram Saved Videos Downloader & Transcriber

A Python tool to download saved videos from Instagram and transcribe them using OpenAI Whisper.
Demo link https://youtu.be/n8UuBiNhkAw
## Features

### Instagram Downloader
- 🔐 Secure login to Instagram
- 📹 Download only video posts from your saved collection
- 🔢 Option to limit number of videos to download
- 📁 Organized output directory
- ✅ Two-factor authentication support
- 📊 Progress tracking and summary

### Video Transcription
- 🎤 Automatic speech-to-text transcription using OpenAI Whisper
- 📊 Metadata extraction (duration, resolution, file size)
- 🌍 Multi-language support with automatic detection
- 📝 Multiple output formats: JSON, TXT, SRT subtitles
- ⚡ Batch processing support
- 🎯 Configurable model sizes (tiny to large)

## Installation

### Requirements
- Python 3.7 or higher
- ffmpeg (for video/audio processing)

### Steps

1. **Install ffmpeg** (if not already installed):
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

2. **Clone or download this repository**

3. **Create virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

5. **Configure credentials** (for Instagram downloader):
```bash
cp .env.example .env
# Edit .env and add your Instagram credentials
```

## Usage

### Basic Usage

Simply run the script:

```bash
python instagram_saved_videos.py
```

The script will prompt you for:
1. Your Instagram username
2. Your Instagram password
3. Maximum number of videos to download (optional)

### Command-Line Arguments

You can also provide arguments directly:

```bash
python instagram_saved_videos.py -u your_username -p your_password -l 5
```

**Options:**
- `-u, --username`: Instagram username
- `-p, --password`: Instagram password
- `-l, --limit`: Maximum number of videos to download
- `-o, --output`: Output directory (default: saved_videos)

**Example with all options:**
```bash
python instagram_saved_videos.py --username myuser --limit 10 --output my_videos
```

### Example

```bash
$ python instagram_saved_videos.py

==================================================
Instagram Saved Videos Downloader
==================================================

Enter your Instagram username: your_username
Enter your Instagram password: ********
Enter max number of videos to download (press Enter for all): 10

Logging in as your_username...
✓ Successfully logged in!

Fetching saved posts...

[1] Downloading video from @someuser...
    Post URL: https://www.instagram.com/p/ABC123/
    ✓ Downloaded successfully!

...

==================================================
Summary:
  Total saved posts checked: 25
  Videos downloaded: 10
  Output directory: /path/to/saved_videos
==================================================
```

## Video Transcription

After downloading videos, you can transcribe them using the included transcription tool.

### Basic Usage

Transcribe all videos in the `saved_videos` directory:
```bash
python transcribe_videos.py
```

Transcribe a specific video:
```bash
python transcribe_videos.py saved_videos/2025-07-22_19-49-28_UTC.mp4
```

### Command-Line Options

```bash
python transcribe_videos.py [video_path] [options]
```

**Options:**
- `-m, --model` - Whisper model size (default: base)
  - `tiny` - Fastest, least accurate (~1GB RAM)
  - `base` - Good balance (default, ~1GB RAM)
  - `small` - Better accuracy (~2GB RAM)
  - `medium` - High accuracy (~5GB RAM)
  - `large` - Best accuracy (~10GB RAM)
- `-o, --output` - Output directory for transcriptions
- `--keep-audio` - Keep extracted audio files
- `--all` - Process all videos in saved_videos directory

**Examples:**
```bash
# Use small model for better accuracy
python transcribe_videos.py -m small

# Process specific directory
python transcribe_videos.py my_videos/ -m base

# Keep audio files and use medium model
python transcribe_videos.py --keep-audio -m medium
```

### Output Files

For each video, three files are generated:

1. **`.json`** - Full transcription with:
   - Complete text
   - Word-by-word timestamps
   - Video metadata
   - Language detection
   - Word count

2. **`.transcript.txt`** - Plain text transcription

3. **`.srt`** - Subtitle file with timestamps (compatible with video players)

### Example Output

```
saved_videos/
├── 2025-07-22_19-49-28_UTC.mp4              # Original video
├── 2025-07-22_19-49-28_UTC.json             # Full data
├── 2025-07-22_19-49-28_UTC.transcript.txt   # Plain text
└── 2025-07-22_19-49-28_UTC.srt              # Subtitles
```

## Output

Videos are saved in the `saved_videos` directory by default. Each video is saved with its Instagram post date and shortcode.

## Security Notes

⚠️ **Important:**
- Never share your Instagram credentials
- Consider using environment variables for credentials in automated scripts
- Instagram may rate-limit or temporarily block accounts that make too many requests
- Use responsibly and respect Instagram's Terms of Service

## Troubleshooting

### Login Issues
- Make sure your username and password are correct
- If you have 2FA enabled, you'll be prompted to enter the code
- Instagram may require additional verification for new login locations

### Download Issues
- Some videos may fail due to privacy settings
- Large collections may take time to process
- Check your internet connection

## Alternative: Using Environment Variables

For repeated use, you can modify the script to use environment variables:

```bash
export IG_USERNAME="your_username"
export IG_PASSWORD="your_password"
```

Then update the script to read from `os.environ.get('IG_USERNAME')`.

## License

This is a simple educational tool. Use responsibly and in accordance with Instagram's Terms of Service.


