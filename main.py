"""
Video to PPT Converter - Main Application
Extract frames from video files and create PowerPoint presentations
"""
import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

# Import project modules
from config.settings import (
    VideoSettings, ImageSettings, PPTSettings, LogSettings,
    SUPPORTED_VIDEO_FORMATS, ensure_directories, validate_settings
)
from src.utils import (
    setup_logging, validate_file_path, generate_output_filename,
    format_duration, format_file_size
)
from src.video_processor import VideoProcessor
from src.image_processor import ImageProcessor
from src.ppt_generator import PPTGenerator

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Extract PPT slides from video and create PowerPoint presentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py video.mp4
  python main.py video.mp4 -o presentation.pptx
  python main.py video.mp4 --interval 10 --no-enhance
  python main.py video.mp4 --title "My Presentation" --author "John Doe"
        """
    )

    # Required arguments
    parser.add_argument(
        'video_path',
        help='Path to input video file'
    )

    # Output options
    parser.add_argument(
        '-o', '--output',
        help='Output PPT file path (auto-generated if not specified)'
    )

    # Processing step control
    parser.add_argument(
        '--start-from',
        choices=['video', 'frames', 'images', 'ppt'],
        default='video',
        help='Start processing from specific step: video=extract frames, frames=process images, images=create PPT, ppt=skip all processing'
    )

    parser.add_argument(
        '--frames-dir',
        help='Directory containing extracted frames (required when --start-from frames/images)'
    )

    parser.add_argument(
        '--images-dir',
        help='Directory containing processed images (required when --start-from images)'
    )

    # Video processing options
    parser.add_argument(
        '--interval',
        type=float,
        default=VideoSettings.FRAME_INTERVAL,
        help=f'Frame extraction interval in seconds (default: {VideoSettings.FRAME_INTERVAL})'
    )

    parser.add_argument(
        '--frame-step',
        type=int,
        help='Extract every N frames (overrides --interval)'
    )

    parser.add_argument(
        '--skip-start',
        type=float,
        default=VideoSettings.SKIP_START_SECONDS,
        help=f'Skip frames at the beginning (seconds, default: {VideoSettings.SKIP_START_SECONDS})'
    )

    parser.add_argument(
        '--skip-end',
        type=float,
        default=VideoSettings.SKIP_END_SECONDS,
        help=f'Skip frames at the end (seconds, default: {VideoSettings.SKIP_END_SECONDS})'
    )

    # Image processing options
    parser.add_argument(
        '--similarity',
        type=float,
        default=ImageSettings.SIMILARITY_THRESHOLD,
        help=f'Similarity threshold for duplicate removal (0-1, default: {ImageSettings.SIMILARITY_THRESHOLD})'
    )

    parser.add_argument(
        '--no-enhance',
        action='store_true',
        help='Skip image enhancement'
    )

    parser.add_argument(
        '--no-dedup',
        action='store_true',
        help='Skip duplicate removal'
    )

    parser.add_argument(
        '--no-filter',
        action='store_true',
        help='Skip PPT content filtering'
    )

    # PPT options
    parser.add_argument(
        '--title',
        help='Presentation title'
    )

    parser.add_argument(
        '--author',
        help='Presentation author'
    )

    parser.add_argument(
        '--add-titles',
        action='store_true',
        help='Add titles to slides'
    )

    parser.add_argument(
        '--template',
        help='Path to PPT template file'
    )

    # Logging options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=LogSettings.LOG_LEVEL,
        help=f'Set logging level (default: {LogSettings.LOG_LEVEL})'
    )

    parser.add_argument(
        '--log-file',
        help='Path to log file'
    )

    return parser.parse_args()

def main():
    """Main application entry point"""
    try:
        # Parse arguments
        args = parse_arguments()

        # Setup logging
        log_file = Path(args.log_file) if args.log_file else LogSettings.LOG_FILE
        logger = setup_logging(
            log_level=args.log_level,
            log_file=log_file,
            verbose=args.verbose
        )

        logger.info("=== Video to PPT Converter Started ===")
        logger.info(f"Starting from step: {args.start_from}")

        # Validate settings
        validate_settings()

        # Ensure output directories exist
        ensure_directories()

        # Validate inputs based on starting step
        video_path = None
        frames_dir = None
        images_dir = None

        if args.start_from == 'video':
            # Validate input video file
            video_path = validate_file_path(args.video_path, SUPPORTED_VIDEO_FORMATS)
            logger.info(f"Video file validated: {video_path}")
        elif args.start_from == 'frames':
            # Validate frames directory
            if not args.frames_dir:
                raise ValueError("--frames-dir is required when starting from 'frames' step")
            frames_dir = Path(args.frames_dir)
            if not frames_dir.exists():
                raise FileNotFoundError(f"Frames directory not found: {frames_dir}")
            logger.info(f"Frames directory validated: {frames_dir}")
        elif args.start_from == 'images':
            # Validate images directory
            if not args.images_dir:
                raise ValueError("--images-dir is required when starting from 'images' step")
            images_dir = Path(args.images_dir)
            if not images_dir.exists():
                raise FileNotFoundError(f"Images directory not found: {images_dir}")
            logger.info(f"Images directory validated: {images_dir}")
        elif args.start_from == 'ppt':
            logger.info("Skipping all processing steps")

        # Generate output filename if not provided
        if args.output:
            output_path = Path(args.output)
        else:
            if args.start_from == 'video':
                output_filename = generate_output_filename(video_path)
            else:
                # Generate filename based on directory or timestamp
                from time import strftime
                timestamp = strftime("%Y%m%d_%H%M%S")
                output_filename = f"presentation_{args.start_from}_{timestamp}.pptx"
            output_path = Path("output/ppt") / output_filename

        logger.info(f"Output PPT: {output_path}")

        # Process based on starting step
        success = process_video_to_ppt_flexible(
            start_from=args.start_from,
            video_path=video_path,
            frames_dir=frames_dir,
            images_dir=images_dir,
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
            logger.info("=== Processing completed successfully ===")
            print(f"\n✅ Success! PPT file created: {output_path}")

            # Show file info
            if output_path.exists():
                file_size = output_path.stat().st_size
                print(f"📄 File size: {format_file_size(file_size)}")
        else:
            logger.error("=== Processing failed ===")
            print("\n❌ Failed to create PPT file. Check the logs for details.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if 'logger' in locals():
            logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

def process_video_to_ppt_flexible(
    start_from: str,
    output_path: Path,
    video_path: Optional[Path] = None,
    frames_dir: Optional[Path] = None,
    images_dir: Optional[Path] = None,
    frame_interval: float = VideoSettings.FRAME_INTERVAL,
    frame_step: Optional[int] = None,
    skip_start: float = VideoSettings.SKIP_START_SECONDS,
    skip_end: float = VideoSettings.SKIP_END_SECONDS,
    similarity_threshold: float = ImageSettings.SIMILARITY_THRESHOLD,
    enhance_images: bool = True,
    remove_duplicates: bool = True,
    filter_ppt_content: bool = True,
    presentation_title: Optional[str] = None,
    presentation_author: Optional[str] = None,
    add_slide_titles: bool = False,
    template_path: Optional[str] = None
) -> bool:
    """
    Flexible pipeline that can start from any step

    Args:
        start_from: Starting step ('video', 'frames', 'images', 'ppt')
        output_path: Path to output PPT file
        video_path: Path to input video file (required for 'video' start)
        frames_dir: Directory containing extracted frames (required for 'frames' start)
        images_dir: Directory containing processed images (required for 'images' start)
        ... (other parameters same as process_video_to_ppt)

    Returns:
        True if successful
    """
    logger = logging.getLogger('v2ppt')

    try:
        processed_images = []

        # Step 1: Extract frames from video (if starting from video)
        if start_from == 'video':
            if not video_path:
                raise ValueError("video_path is required when starting from 'video'")

            logger.info("Step 1: Extracting frames from video")

            with VideoProcessor(str(video_path)) as video_processor:
                # Get video info
                video_info = video_processor.get_video_info()
                logger.info(f"Video duration: {format_duration(video_info['duration'])}")

                # Extract frames
                frames_dir = Path("output/frames") / video_path.stem
                extracted_frames = video_processor.extract_frames(
                    output_dir=frames_dir,
                    frame_interval=frame_interval,
                    frame_step=frame_step,
                    skip_start=skip_start,
                    skip_end=skip_end
                )

            if not extracted_frames:
                logger.error("No frames were extracted from the video")
                return False

        # Step 2: Process images (if starting from video or frames)
        if start_from in ['video', 'frames']:
            if start_from == 'frames':
                if not frames_dir:
                    raise ValueError("frames_dir is required when starting from 'frames'")

                # Find all image files in frames directory
                extracted_frames = []
                for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
                    extracted_frames.extend(frames_dir.glob(f'*{ext}'))
                    extracted_frames.extend(frames_dir.glob(f'*{ext.upper()}'))

                if not extracted_frames:
                    logger.error(f"No image files found in frames directory: {frames_dir}")
                    return False

                logger.info(f"Found {len(extracted_frames)} frames in directory: {frames_dir}")

            logger.info("Step 2: Processing extracted images")

            image_processor = ImageProcessor()
            processed_images = image_processor.process_images(
                image_paths=extracted_frames,
                output_dir=frames_dir / "processed" if frames_dir else Path("output/frames/processed"),
                enhance=enhance_images,
                remove_duplicates=remove_duplicates,
                filter_ppt=filter_ppt_content
            )

            if not processed_images:
                logger.error("No images remained after processing")
                return False

        # Step 3: Use existing processed images (if starting from images)
        elif start_from == 'images':
            if not images_dir:
                raise ValueError("images_dir is required when starting from 'images'")

            # Find all image files in images directory
            processed_images = []
            for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
                processed_images.extend(images_dir.glob(f'*{ext}'))
                processed_images.extend(images_dir.glob(f'*{ext.upper()}'))

            if not processed_images:
                logger.error(f"No image files found in images directory: {images_dir}")
                return False

            logger.info(f"Found {len(processed_images)} processed images in directory: {images_dir}")

        # Step 4: Create PowerPoint presentation (unless starting from ppt)
        if start_from != 'ppt':
            logger.info("Step 3: Creating PowerPoint presentation")

            template_path_obj = Path(template_path) if template_path else None
            ppt_generator = PPTGenerator(template_path=template_path_obj)

            # Set presentation properties
            if presentation_title or presentation_author:
                ppt_generator.set_presentation_properties(
                    title=presentation_title or f"Extracted from {start_from}",
                    author=presentation_author,
                    subject="Video Frame Extraction",
                    comments=f"Generated from {start_from} using v2ppt"
                )

            # Create presentation
            success = ppt_generator.create_presentation_from_images(
                image_paths=processed_images,
                output_path=output_path,
                add_titles=add_slide_titles,
                title_prefix="Slide"
            )

            return success
        else:
            logger.info("Skipping PPT creation as requested")
            return True

    except Exception as e:
        logger.error(f"Error in processing pipeline: {e}", exc_info=True)
        return False


def process_video_to_ppt(
    video_path: Path,
    output_path: Path,
    frame_interval: float = VideoSettings.FRAME_INTERVAL,
    frame_step: Optional[int] = None,
    skip_start: float = VideoSettings.SKIP_START_SECONDS,
    skip_end: float = VideoSettings.SKIP_END_SECONDS,
    similarity_threshold: float = ImageSettings.SIMILARITY_THRESHOLD,
    enhance_images: bool = True,
    remove_duplicates: bool = True,
    filter_ppt_content: bool = True,
    presentation_title: Optional[str] = None,
    presentation_author: Optional[str] = None,
    add_slide_titles: bool = False,
    template_path: Optional[str] = None
) -> bool:
    """
    Complete pipeline to process video and create PPT (legacy function)

    This function is kept for backward compatibility and calls the flexible version.
    """
    return process_video_to_ppt_flexible(
        start_from='video',
        video_path=video_path,
        output_path=output_path,
        frame_interval=frame_interval,
        frame_step=frame_step,
        skip_start=skip_start,
        skip_end=skip_end,
        similarity_threshold=similarity_threshold,
        enhance_images=enhance_images,
        remove_duplicates=remove_duplicates,
        filter_ppt_content=filter_ppt_content,
        presentation_title=presentation_title,
        presentation_author=presentation_author,
        add_slide_titles=add_slide_titles,
        template_path=template_path
    )

if __name__ == "__main__":
    main()
