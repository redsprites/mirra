#!/usr/bin/env python3
"""
Video Transcription Script
Extracts audio from videos and transcribes using OpenAI Whisper
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import whisper
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy import VideoFileClip
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')


class VideoTranscriber:
    def __init__(self, model_size="base", quiet=False):
        """
        Initialize the transcriber with a Whisper model.
        
        Args:
            model_size (str): Whisper model size (tiny, base, small, medium, large)
                             tiny: Fastest, least accurate
                             base: Good balance (default)
                             small: Better accuracy
                             medium: High accuracy
                             large: Best accuracy, slowest
            quiet (bool): Suppress per-step progress output (for parallel workers)
        """
        self.model_size = model_size
        self.model = None
        self.quiet = quiet

    def _log(self, message):
        if not self.quiet:
            print(message)
        
    def load_model(self):
        """Load the Whisper model."""
        if self.model is None:
            self._log("⏳ Loading Whisper model... (first time may take a while)")
            self.model = whisper.load_model(self.model_size)
            self._log("✓ Model loaded successfully!")
    
    def extract_metadata(self, video_path):
        """
        Extract metadata from video file.
        
        Args:
            video_path (Path): Path to video file
            
        Returns:
            dict: Video metadata
        """
        self._log("\n" + "="*50)
        self._log("📊 Extracting metadata")
        self._log("="*50)
        
        try:
            video = VideoFileClip(str(video_path))
            
            metadata = {
                "filename": video_path.name,
                "duration_seconds": video.duration,
                "duration_formatted": self._format_duration(video.duration),
                "fps": video.fps,
                "size": video.size,
                "audio_fps": video.audio.fps if video.audio else None,
                "file_size_mb": video_path.stat().st_size / (1024 * 1024),
                "processed_date": datetime.now().isoformat()
            }
            
            video.close()
            
            # Try to extract username from txt file if it exists
            txt_file = video_path.with_suffix('.txt')
            if txt_file.exists():
                with open(txt_file, 'r') as f:
                    content = f.read()
                    # Look for username in the txt file
                    for line in content.split('\n'):
                        if line.strip():
                            metadata['source'] = line.strip()
                            break
            
            self._log("✓ Metadata extracted:")
            self._log(f"  Duration: {metadata['duration_formatted']}")
            self._log(f"  Size: {metadata['file_size_mb']:.2f} MB")
            self._log(f"  Resolution: {metadata['size']}")
            if 'source' in metadata:
                self._log(f"  Source: {metadata['source']}")
            
            return metadata
            
        except Exception as e:
            self._log(f"✗ Error extracting metadata: {e}")
            return {"filename": video_path.name, "error": str(e)}
    
    def extract_audio(self, video_path, audio_path):
        """
        Extract audio from video file.
        
        Args:
            video_path (Path): Path to video file
            audio_path (Path): Path to save audio file
            
        Returns:
            bool: Success status
        """
        self._log("\n" + "="*50)
        self._log("🎵 Extracting audio from video")
        self._log("="*50)
        
        try:
            video = VideoFileClip(str(video_path))
            
            if video.audio is None:
                self._log("✗ Video has no audio track")
                video.close()
                return False
            
            self._log("⏳ Extracting audio...")
            video.audio.write_audiofile(
                str(audio_path),
                codec='pcm_s16le',
                logger=None
            )
            
            video.close()
            self._log("✓ Audio extracted successfully")
            return True
            
        except Exception as e:
            self._log(f"✗ Error extracting audio: {e}")
            return False
    
    def transcribe(self, audio_path, video_metadata=None):
        """
        Transcribe audio file using Whisper.
        
        Args:
            audio_path (Path): Path to audio file
            video_metadata (dict): Optional video metadata
            
        Returns:
            dict: Transcription results
        """
        self._log("\n" + "="*50)
        self._log("🎤 Transcribing audio with Whisper")
        self._log("="*50)
        
        self.load_model()
        
        try:
            self._log("⏳ Processing audio... (this may take a while)")
            
            # Transcribe with Whisper
            result = self.model.transcribe(
                str(audio_path),
                verbose=False,
                fp16=False  # Use FP32 for better compatibility
            )
            
            # Count words
            word_count = len(result['text'].split())
            
            self._log("✓ Transcription complete!")
            self._log(f"  Words: {word_count}")
            self._log(f"  Language: {result.get('language', 'unknown')}")
            
            # Prepare output
            transcription_data = {
                "text": result['text'],
                "language": result.get('language'),
                "word_count": word_count,
                "segments": result.get('segments', []),
                "metadata": video_metadata,
                "transcription_date": datetime.now().isoformat(),
                "model": self.model_size
            }
            
            return transcription_data
            
        except Exception as e:
            self._log(f"✗ Error during transcription: {e}")
            return None
    
    def save_transcription(self, transcription_data, output_path):
        """
        Save transcription to file.
        
        Args:
            transcription_data (dict): Transcription data
            output_path (Path): Path to save transcription
        """
        self._log("\n" + "="*50)
        self._log("💾 Saving transcription")
        self._log("="*50)
        
        try:
            # Save JSON with full data
            json_path = output_path.with_suffix('.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(transcription_data, f, indent=2, ensure_ascii=False)
            self._log(f"✓ Full transcription saved: {json_path.name}")
            
            # Save plain text version
            txt_path = output_path.with_suffix('.transcript.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(transcription_data['text'])
            self._log(f"✓ Text-only version saved: {txt_path.name}")
            
            # Save formatted version with timestamps
            srt_path = output_path.with_suffix('.srt')
            self._save_srt(transcription_data['segments'], srt_path)
            self._log(f"✓ Subtitles saved: {srt_path.name}")
            
        except Exception as e:
            self._log(f"✗ Error saving transcription: {e}")
    
    def _save_srt(self, segments, srt_path):
        """Save transcription as SRT subtitle file."""
        try:
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments, start=1):
                    start_time = self._format_timestamp(segment['start'])
                    end_time = self._format_timestamp(segment['end'])
                    text = segment['text'].strip()
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")
        except Exception as e:
            if not self.quiet:
                print(f"⚠️  Could not save SRT file: {e}")
    
    def _format_timestamp(self, seconds):
        """Format seconds to SRT timestamp format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_duration(self, seconds):
        """Format duration in seconds to human-readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def process_video(self, video_path, output_dir=None, keep_audio=False):
        """
        Complete pipeline: extract metadata, audio, and transcribe.
        
        Args:
            video_path (Path): Path to video file
            output_dir (Path): Directory to save outputs (default: same folder as video)
            keep_audio (bool): Keep extracted audio file
            
        Returns:
            dict: Processing results
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            self._log(f"✗ Video file not found: {video_path}")
            return None
        
        # By default, save transcription in the same folder as the video
        if output_dir is None:
            output_dir = video_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        self._log("\n" + "="*60)
        self._log(f"🎬 Processing: {video_path.name}")
        self._log("="*60)
        
        # Step 1: Extract metadata
        metadata = self.extract_metadata(video_path)
        
        # Step 2: Extract audio
        audio_path = output_dir / f"{video_path.stem}_audio.wav"
        if not self.extract_audio(video_path, audio_path):
            return None
        
        # Step 3: Transcribe
        transcription = self.transcribe(audio_path, metadata)
        
        if transcription is None:
            return None
        
        # Step 4: Save results
        output_path = output_dir / video_path.stem
        self.save_transcription(transcription, output_path)
        
        # Clean up audio file if requested
        if not keep_audio and audio_path.exists():
            audio_path.unlink()
            self._log("🗑️  Removed temporary audio file")
        
        self._log("\n" + "="*60)
        self._log("✅ Processing complete!")
        self._log("="*60)
        if not self.quiet:
            print(f"\n📄 Transcription preview:")
            print("-" * 60)
            preview = transcription['text'][:500]
            print(preview + ("..." if len(transcription['text']) > 500 else ""))
            print("-" * 60)
        
        return transcription


def has_transcription(video_path):
    """Return True if this video already has a transcript file."""
    return video_path.with_suffix('.transcript.txt').exists()


def process_video_worker(args):
    """Worker for parallel transcription (one Whisper model per process)."""
    video_path_str, model_size, output_dir, keep_audio = args
    video_path = Path(video_path_str)
    transcriber = VideoTranscriber(model_size=model_size, quiet=True)
    result = transcriber.process_video(
        video_path,
        output_dir=output_dir,
        keep_audio=keep_audio,
    )
    if result:
        return {
            'video': video_path.name,
            'words': result['word_count'],
            'language': result['language'],
            'error': None,
        }
    return {
        'video': video_path.name,
        'words': 0,
        'language': None,
        'error': 'processing failed',
    }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Transcribe video files using OpenAI Whisper'
    )
    parser.add_argument(
        'video',
        nargs='?',
        help='Path to video file or directory containing videos'
    )
    parser.add_argument(
        '-m', '--model',
        default='base',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help='Whisper model size (default: base)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output directory (default: same as video)'
    )
    parser.add_argument(
        '--keep-audio',
        action='store_true',
        help='Keep extracted audio files'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all videos in saved_videos directory'
    )
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=1,
        help='Parallel workers for transcription (default: 1, try 2-4 on multi-core machines)'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip videos that already have a .transcript.txt file'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("🎙️  Video Transcription Tool")
    print("="*60)
    
    # Initialize transcriber (single-worker mode only)
    transcriber = None
    
    # Determine which videos to process
    videos_to_process = []
    
    if args.all:
        # Process all videos in saved_videos directory (including subfolders)
        saved_videos_dir = Path('saved_videos')
        if saved_videos_dir.exists():
            # Look for videos in subfolders and root
            videos_to_process = list(saved_videos_dir.glob('**/*.mp4'))
            print(f"\n📁 Found {len(videos_to_process)} video(s) in saved_videos/")
        else:
            print("✗ saved_videos directory not found")
            return
    elif args.video:
        video_path = Path(args.video)
        if video_path.is_dir():
            # Recursively find all mp4 files
            videos_to_process = list(video_path.glob('**/*.mp4'))
            print(f"\n📁 Found {len(videos_to_process)} video(s) in {video_path}")
        else:
            videos_to_process = [video_path]
    else:
        # Default: look for videos in saved_videos (including subfolders)
        saved_videos_dir = Path('saved_videos')
        if saved_videos_dir.exists():
            videos_to_process = list(saved_videos_dir.glob('**/*.mp4'))
            if videos_to_process:
                print(f"\n📁 Found {len(videos_to_process)} video(s) in saved_videos/")
                print("Processing all videos (use specific path to process only one)")
            else:
                print("✗ No videos found in saved_videos directory")
                return
        else:
            print("✗ No video specified and saved_videos directory not found")
            parser.print_help()
            return
    
    if not videos_to_process:
        print("✗ No videos to process")
        return

    if args.skip_existing:
        skipped = [v for v in videos_to_process if has_transcription(v)]
        videos_to_process = [v for v in videos_to_process if not has_transcription(v)]
        if skipped:
            print(f"⏭️  Skipping {len(skipped)} video(s) with existing transcriptions")

    if not videos_to_process:
        print("✓ All videos already transcribed")
        return

    workers = max(1, args.workers)
    if workers > 1:
        workers = min(workers, len(videos_to_process), cpu_count() or 1)

    results = []
    failed = []

    if workers == 1:
        transcriber = VideoTranscriber(model_size=args.model)
        print(f"🔧 Initializing Whisper model: {args.model}")
        for i, video_path in enumerate(videos_to_process, 1):
            print(f"\n\n{'='*60}")
            print(f"Video {i}/{len(videos_to_process)}")
            print(f"{'='*60}")

            result = transcriber.process_video(
                video_path,
                output_dir=args.output,
                keep_audio=args.keep_audio,
            )

            if result:
                results.append({
                    'video': video_path.name,
                    'words': result['word_count'],
                    'language': result['language'],
                })
            else:
                failed.append(video_path.name)
    else:
        print(f"⚡ Processing {len(videos_to_process)} video(s) with {workers} workers (model: {args.model})")
        worker_args = [
            (str(video_path), args.model, args.output, args.keep_audio)
            for video_path in videos_to_process
        ]
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(process_video_worker, job): job[0]
                for job in worker_args
            }
            for i, future in enumerate(as_completed(futures), 1):
                video_name = Path(futures[future]).name
                try:
                    result = future.result()
                    if result.get('error'):
                        failed.append(video_name)
                        print(f"[{i}/{len(videos_to_process)}] ✗ {video_name}")
                    else:
                        results.append(result)
                        print(
                            f"[{i}/{len(videos_to_process)}] ✓ {result['video']}: "
                            f"{result['words']} words ({result['language']})"
                        )
                except Exception as e:
                    failed.append(video_name)
                    print(f"[{i}/{len(videos_to_process)}] ✗ {video_name}: {e}")
    
    # Final summary
    if results or failed:
        print("\n\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(f"Videos processed: {len(results)}")
        if failed:
            print(f"Failed: {len(failed)}")
        if results:
            print(f"Total words transcribed: {sum(r['words'] for r in results)}")
            print("\nIndividual results:")
            for r in sorted(results, key=lambda r: r['video']):
                print(f"  • {r['video']}: {r['words']} words ({r['language']})")
        if failed:
            print("\nFailed videos:")
            for name in failed:
                print(f"  • {name}")
        print("="*60)


if __name__ == "__main__":
    main()

