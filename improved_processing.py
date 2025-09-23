#!/usr/bin/env python3
"""
Improved PPT processing with better control over filtering and deduplication
"""
import sys
import argparse
from pathlib import Path
import logging

# Add src to path
sys.path.append('src')
sys.path.append('config')

from main import process_video_to_ppt_flexible
from config.settings import VideoSettings, ImageSettings

def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(
        description="Improved v2ppt with better PPT page preservation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Conservative processing (preserve more slides)
  python improved_processing.py video.mp4 --conservative
  
  # Very conservative (minimal filtering)
  python improved_processing.py video.mp4 --very-conservative
  
  # Custom thresholds
  python improved_processing.py video.mp4 --similarity 0.6 --interval 3
  
  # Disable all filtering
  python improved_processing.py video.mp4 --no-filter --no-dedup
  
  # Start from existing frames
  python improved_processing.py dummy.mp4 --start-from frames --frames-dir path/to/frames --conservative
        """
    )
    
    # Input/Output
    parser.add_argument('video_path', help='Input video file path')
    parser.add_argument('-o', '--output', help='Output PPT file path')
    
    # Processing step control
    parser.add_argument('--start-from', choices=['video', 'frames', 'images', 'ppt'],
                       default='video', help='Start processing from specific step')
    parser.add_argument('--frames-dir', help='Directory containing extracted frames')
    parser.add_argument('--images-dir', help='Directory containing processed images')
    
    # Preset modes
    parser.add_argument('--conservative', action='store_true',
                       help='Conservative mode: preserve more slides (similarity=0.7, less strict PPT detection)')
    parser.add_argument('--very-conservative', action='store_true',
                       help='Very conservative: minimal filtering (similarity=0.6, no PPT filtering)')
    parser.add_argument('--aggressive', action='store_true',
                       help='Aggressive mode: more filtering (similarity=0.9, strict PPT detection)')
    
    # Video processing
    parser.add_argument('--interval', type=float, default=VideoSettings.FRAME_INTERVAL,
                       help=f'Frame extraction interval in seconds (default: {VideoSettings.FRAME_INTERVAL})')
    parser.add_argument('--frame-step', type=int, help='Extract every N frames (overrides --interval)')
    parser.add_argument('--skip-start', type=float, default=VideoSettings.SKIP_START_SECONDS,
                       help=f'Skip frames at the beginning (seconds, default: {VideoSettings.SKIP_START_SECONDS})')
    parser.add_argument('--skip-end', type=float, default=VideoSettings.SKIP_END_SECONDS,
                       help=f'Skip frames at the end (seconds, default: {VideoSettings.SKIP_END_SECONDS})')
    
    # Image processing
    parser.add_argument('--similarity', type=float, default=ImageSettings.SIMILARITY_THRESHOLD,
                       help=f'Similarity threshold for duplicate detection (default: {ImageSettings.SIMILARITY_THRESHOLD})')
    parser.add_argument('--no-enhance', action='store_true', help='Skip image enhancement')
    parser.add_argument('--no-dedup', action='store_true', help='Skip duplicate removal')
    parser.add_argument('--no-filter', action='store_true', help='Skip PPT content filtering')
    
    # PPT generation
    parser.add_argument('--title', help='Presentation title')
    parser.add_argument('--author', help='Presentation author')
    parser.add_argument('--add-titles', action='store_true', help='Add titles to slides')
    parser.add_argument('--template', help='PPT template file path')
    
    # Logging
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Log level')
    parser.add_argument('--log-file', help='Log file path')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose or args.log_level == 'DEBUG')
    
    # Apply preset modes
    if args.very_conservative:
        args.similarity = 0.6
        args.no_filter = True
        args.interval = min(args.interval, 3.0)  # More frequent extraction
        print("🛡️  Very Conservative Mode: similarity=0.6, no PPT filtering, interval≤3s")
        
    elif args.conservative:
        args.similarity = 0.7
        args.interval = min(args.interval, 4.0)  # Slightly more frequent extraction
        print("🛡️  Conservative Mode: similarity=0.7, interval≤4s")
        
    elif args.aggressive:
        args.similarity = 0.9
        args.interval = max(args.interval, 8.0)  # Less frequent extraction
        print("⚡ Aggressive Mode: similarity=0.9, interval≥8s")
    
    # Validate inputs
    video_path = Path(args.video_path)
    if args.start_from == 'video' and not video_path.exists():
        print(f"❌ Video file not found: {video_path}")
        return 1
    
    if args.start_from == 'frames' and not args.frames_dir:
        print("❌ --frames-dir is required when starting from 'frames'")
        return 1
        
    if args.start_from == 'images' and not args.images_dir:
        print("❌ --images-dir is required when starting from 'images'")
        return 1
    
    # Generate output path
    if args.output:
        output_path = Path(args.output)
    else:
        if args.start_from == 'video':
            base_name = video_path.stem
        else:
            from time import strftime
            timestamp = strftime("%Y%m%d_%H%M%S")
            base_name = f"presentation_{args.start_from}_{timestamp}"
        
        mode_suffix = ""
        if args.very_conservative:
            mode_suffix = "_very_conservative"
        elif args.conservative:
            mode_suffix = "_conservative"
        elif args.aggressive:
            mode_suffix = "_aggressive"
            
        output_path = Path("output/ppt") / f"{base_name}{mode_suffix}.pptx"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🎬 Improved v2ppt Processing")
    print(f"Input: {args.video_path}")
    print(f"Output: {output_path}")
    print(f"Start from: {args.start_from}")
    print(f"Similarity threshold: {args.similarity}")
    print(f"Frame interval: {args.interval}s")
    print(f"Enhance images: {not args.no_enhance}")
    print(f"Remove duplicates: {not args.no_dedup}")
    print(f"Filter PPT content: {not args.no_filter}")
    
    # Process
    try:
        success = process_video_to_ppt_flexible(
            start_from=args.start_from,
            video_path=video_path if args.start_from == 'video' else None,
            frames_dir=Path(args.frames_dir) if args.frames_dir else None,
            images_dir=Path(args.images_dir) if args.images_dir else None,
            output_path=output_path,
            frame_interval=args.interval,
            frame_step=args.frame_step,
            skip_start=args.skip_start,
            skip_end=args.skip_end,
            similarity_threshold=args.similarity,
            enhance_images=not args.no_enhance,
            remove_duplicates=not args.no_dedup,
            filter_ppt_content=not args.no_filter,
            presentation_title=args.title,
            presentation_author=args.author,
            add_slide_titles=args.add_titles,
            template_path=args.template
        )
        
        if success:
            print(f"\n✅ Processing completed successfully!")
            print(f"📄 Output file: {output_path}")
            
            if output_path.exists():
                size = output_path.stat().st_size
                print(f"📊 File size: {size:,} bytes")
            
            # Provide recommendations
            print(f"\n💡 Tips for better results:")
            if not args.conservative and not args.very_conservative:
                print("   • Try --conservative mode if slides are missing")
                print("   • Try --very-conservative for maximum slide preservation")
            if args.similarity > 0.8:
                print(f"   • Lower --similarity threshold (current: {args.similarity}) to keep more slides")
            if args.interval > 5:
                print(f"   • Lower --interval (current: {args.interval}s) to capture more frames")
                
        else:
            print(f"\n❌ Processing failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
