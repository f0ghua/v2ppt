"""
Image processing module for optimizing and deduplicating extracted frames
"""
import cv2
import numpy as np
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from PIL import Image, ImageEnhance
import hashlib

from config.settings import ImageSettings
from src.utils import ProgressTracker

logger = logging.getLogger('v2ppt.image')

class ImageProcessor:
    """
    Image processor for optimizing and deduplicating frames
    """
    
    def __init__(self):
        """Initialize image processor"""
        self.processed_hashes = set()
        self.similarity_cache = {}
    
    def enhance_image(self, image_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Enhance image quality (brightness, contrast, sharpness)
        
        Args:
            image_path: Path to input image
            output_path: Path to save enhanced image (optional)
            
        Returns:
            Path to enhanced image
        """
        if output_path is None:
            output_path = image_path.parent / f"enhanced_{image_path.name}"
        
        try:
            # Open image with PIL
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Apply enhancements
                if ImageSettings.ENHANCE_BRIGHTNESS != 1.0:
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(ImageSettings.ENHANCE_BRIGHTNESS)
                
                if ImageSettings.ENHANCE_CONTRAST != 1.0:
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(ImageSettings.ENHANCE_CONTRAST)
                
                if ImageSettings.ENHANCE_SHARPNESS != 1.0:
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(ImageSettings.ENHANCE_SHARPNESS)
                
                # Resize if necessary
                img = self._resize_image(img)
                
                # Save enhanced image
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                if ImageSettings.OUTPUT_FORMAT.upper() == 'JPEG':
                    img.save(output_path, 'JPEG', quality=ImageSettings.JPEG_QUALITY, optimize=True)
                else:
                    img.save(output_path, ImageSettings.OUTPUT_FORMAT, optimize=True)
                
                logger.debug(f"Enhanced image saved: {output_path.name}")
                return output_path
                
        except Exception as e:
            logger.error(f"Failed to enhance image {image_path}: {e}")
            return image_path
    
    def _resize_image(self, img: Image.Image) -> Image.Image:
        """
        Resize image if it exceeds maximum dimensions
        
        Args:
            img: PIL Image object
            
        Returns:
            Resized image
        """
        width, height = img.size
        max_width = ImageSettings.MAX_WIDTH
        max_height = ImageSettings.MAX_HEIGHT
        
        if width <= max_width and height <= max_height:
            return img
        
        if ImageSettings.MAINTAIN_ASPECT_RATIO:
            # Calculate scaling factor
            scale_w = max_width / width
            scale_h = max_height / height
            scale = min(scale_w, scale_h)
            
            new_width = int(width * scale)
            new_height = int(height * scale)
        else:
            new_width = min(width, max_width)
            new_height = min(height, max_height)
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def calculate_image_hash(self, image_path: Path, hash_size: int = 16) -> str:
        """
        Calculate improved perceptual hash optimized for PPT content

        Args:
            image_path: Path to image file
            hash_size: Size of the hash (default: 16x16 = 256 bits for better precision)

        Returns:
            Hexadecimal hash string
        """
        try:
            # Read image with OpenCV
            img = cv2.imread(str(image_path))
            if img is None:
                raise ValueError(f"Cannot read image: {image_path}")

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur to reduce noise but preserve structure
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)

            # Resize to hash_size x hash_size
            resized = cv2.resize(blurred, (hash_size, hash_size), interpolation=cv2.INTER_AREA)

            # Use DCT (Discrete Cosine Transform) for better frequency domain analysis
            # This is more robust for text-heavy images like PPT slides
            dct = cv2.dct(np.float32(resized))

            # Take only the top-left 8x8 portion (low frequency components)
            dct_low_freq = dct[:8, :8]

            # Calculate median instead of mean for better threshold
            median = np.median(dct_low_freq)

            # Create binary hash based on DCT coefficients
            binary_hash = dct_low_freq > median

            # Convert to hexadecimal string
            hash_string = ''.join(['1' if pixel else '0' for pixel in binary_hash.flatten()])
            return hex(int(hash_string, 2))[2:].zfill(len(hash_string) // 4)

        except Exception as e:
            logger.error(f"Failed to calculate hash for {image_path}: {e}")
            return ""
    
    def calculate_similarity(self, hash1: str, hash2: str) -> float:
        """
        Calculate similarity between two image hashes
        
        Args:
            hash1: First image hash
            hash2: Second image hash
            
        Returns:
            Similarity score (0-1, where 1 is identical)
        """
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return 0.0
        
        # Convert hex to binary
        try:
            bin1 = bin(int(hash1, 16))[2:].zfill(len(hash1) * 4)
            bin2 = bin(int(hash2, 16))[2:].zfill(len(hash2) * 4)
        except ValueError:
            return 0.0
        
        # Calculate Hamming distance
        hamming_distance = sum(c1 != c2 for c1, c2 in zip(bin1, bin2))
        
        # Convert to similarity (0-1)
        max_distance = len(bin1)
        similarity = 1.0 - (hamming_distance / max_distance)
        
        return similarity
    
    def calculate_content_features(self, image_path: Path) -> Dict:
        """
        Calculate additional content features for better duplicate detection

        Args:
            image_path: Path to image file

        Returns:
            Dictionary of content features
        """
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return {}

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Feature 1: Text density (edge density in text-likely regions)
            edges = cv2.Canny(gray, 50, 150)
            text_density = np.sum(edges) / (edges.shape[0] * edges.shape[1])

            # Feature 2: Color histogram (simplified)
            hist = cv2.calcHist([gray], [0], None, [16], [0, 256])  # 16 bins
            hist_normalized = hist.flatten() / hist.sum()

            # Feature 3: Structural features
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            num_contours = len([c for c in contours if cv2.contourArea(c) > 100])

            return {
                'text_density': text_density,
                'hist': hist_normalized,
                'num_contours': num_contours
            }

        except Exception as e:
            logger.debug(f"Failed to calculate content features for {image_path}: {e}")
            return {}

    def calculate_advanced_similarity(self, path1: Path, path2: Path,
                                    hash1: str, hash2: str) -> float:
        """
        Calculate advanced similarity using multiple features

        Args:
            path1, path2: Image file paths
            hash1, hash2: Perceptual hashes

        Returns:
            Combined similarity score (0-1)
        """
        # Base similarity from perceptual hash
        hash_similarity = self.calculate_similarity(hash1, hash2)

        # Get content features
        features1 = self.calculate_content_features(path1)
        features2 = self.calculate_content_features(path2)

        if not features1 or not features2:
            return hash_similarity

        # Feature similarities
        similarities = [hash_similarity]

        # Text density similarity
        if 'text_density' in features1 and 'text_density' in features2:
            density_diff = abs(features1['text_density'] - features2['text_density'])
            density_sim = 1.0 - min(density_diff / 0.1, 1.0)  # Normalize
            similarities.append(density_sim)

        # Histogram similarity
        if 'hist' in features1 and 'hist' in features2:
            hist_correlation = cv2.compareHist(
                features1['hist'].astype(np.float32),
                features2['hist'].astype(np.float32),
                cv2.HISTCMP_CORREL
            )
            hist_sim = max(0, hist_correlation)  # Ensure non-negative
            similarities.append(hist_sim)

        # Contour count similarity
        if 'num_contours' in features1 and 'num_contours' in features2:
            count_diff = abs(features1['num_contours'] - features2['num_contours'])
            max_count = max(features1['num_contours'], features2['num_contours'], 1)
            count_sim = 1.0 - (count_diff / max_count)
            similarities.append(count_sim)

        # Weighted average (hash gets more weight)
        weights = [0.5, 0.2, 0.2, 0.1][:len(similarities)]
        weighted_sim = sum(s * w for s, w in zip(similarities, weights)) / sum(weights)

        return weighted_sim

    def remove_duplicates(self, image_paths: List[Path],
                         similarity_threshold: Optional[float] = None,
                         progress_callback: Optional[callable] = None) -> List[Path]:
        """
        Remove duplicate and similar images using advanced similarity detection

        Args:
            image_paths: List of image file paths
            similarity_threshold: Similarity threshold for duplicate detection
            progress_callback: Optional callback function for progress updates (current, total)

        Returns:
            List of unique image paths
        """
        if similarity_threshold is None:
            similarity_threshold = ImageSettings.SIMILARITY_THRESHOLD

        if not image_paths:
            return []

        logger.info(f"Removing duplicates from {len(image_paths)} images")
        logger.info(f"Similarity threshold: {similarity_threshold}")

        # Calculate hashes for all images
        image_hashes = {}
        progress = ProgressTracker(len(image_paths), "Calculating image hashes")

        for i, img_path in enumerate(image_paths):
            img_hash = self.calculate_image_hash(img_path)
            if img_hash:
                image_hashes[img_path] = img_hash
            progress.update()

            # Call external progress callback for hash calculation (first half)
            if progress_callback:
                hash_progress = (i + 1) / len(image_paths) * 0.5  # 50% for hash calculation
                progress_callback(hash_progress, 1.0)

        # Find unique images using advanced similarity
        unique_images = []
        processed_images = []

        progress = ProgressTracker(len(image_hashes), "Finding unique images")
        image_items = list(image_hashes.items())

        for i, (img_path, img_hash) in enumerate(image_items):
            is_duplicate = False
            best_similarity = 0.0

            # Check against already processed images
            for processed_path, processed_hash in processed_images:
                similarity = self.calculate_advanced_similarity(
                    img_path, processed_path, img_hash, processed_hash
                )

                if similarity >= similarity_threshold:
                    is_duplicate = True
                    best_similarity = similarity
                    logger.debug(f"Duplicate found: {img_path.name} vs {processed_path.name} "
                               f"(similarity: {similarity:.3f})")
                    break

                best_similarity = max(best_similarity, similarity)

            if not is_duplicate:
                unique_images.append(img_path)
                processed_images.append((img_path, img_hash))
                logger.debug(f"Unique image: {img_path.name} (max similarity: {best_similarity:.3f})")

            progress.update()

            # Call external progress callback for similarity detection (second half)
            if progress_callback:
                similarity_progress = 0.5 + (i + 1) / len(image_items) * 0.5  # 50-100%
                progress_callback(similarity_progress, 1.0)

        removed_count = len(image_paths) - len(unique_images)
        logger.info(f"Removed {removed_count} duplicate images")
        logger.info(f"Remaining unique images: {len(unique_images)}")

        return unique_images
    
    def detect_ppt_content(self, image_path: Path) -> bool:
        """
        Improved PPT content detection with multiple heuristics

        Args:
            image_path: Path to image file

        Returns:
            True if image likely contains PPT content
        """
        try:
            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                return False

            height, width = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Heuristic 1: Check aspect ratio (PPT slides are usually 16:9 or 4:3)
            aspect_ratio = width / height
            is_slide_ratio = (1.2 < aspect_ratio < 2.0)  # More lenient range

            # Heuristic 2: Check for structured content using edge detection
            edges = cv2.Canny(gray, 30, 100)  # Lower thresholds for better text detection

            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Analyze contours for text and structured elements
            text_like_contours = 0
            large_rectangular_areas = 0

            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 50:  # Lower minimum area
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio_contour = w / h if h > 0 else 0

                    # Text-like elements (horizontal text lines)
                    if 50 < area < 5000 and 1.5 < aspect_ratio_contour < 20:
                        text_like_contours += 1

                    # Large rectangular areas (content blocks, images)
                    if area > 1000 and 0.3 < aspect_ratio_contour < 5:
                        large_rectangular_areas += 1

            # Heuristic 3: Check color distribution
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])

            # Check for background uniformity (PPT slides often have uniform backgrounds)
            background_pixels = hist[240:256].sum() + hist[0:16].sum()  # Very light or very dark
            total_pixels = hist.sum()
            background_ratio = background_pixels / total_pixels if total_pixels > 0 else 0

            # Check for distinct color peaks (text, graphics)
            normalized_hist = hist / total_pixels if total_pixels > 0 else hist
            significant_peaks = np.sum(normalized_hist > 0.05)  # Colors that make up >5% of image

            # Heuristic 4: Check for horizontal and vertical lines (slide structure)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))

            horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, vertical_kernel)

            has_structure = (np.sum(horizontal_lines) + np.sum(vertical_lines)) > 1000

            # Scoring system (more lenient)
            score = 0

            # Basic content indicators
            if text_like_contours >= 3:  # Reduced from 5
                score += 2
            elif text_like_contours >= 1:
                score += 1

            if large_rectangular_areas >= 1:
                score += 1

            if significant_peaks >= 2:  # Reduced from 3
                score += 1

            if 0.1 < background_ratio < 0.8:  # Has some background but not too much
                score += 1

            if has_structure:
                score += 1

            if is_slide_ratio:
                score += 1

            # More lenient threshold: accept if score >= 3 (was effectively 2 before)
            is_ppt_content = score >= 3

            logger.debug(f"PPT detection for {image_path.name}: score={score}, "
                        f"text_contours={text_like_contours}, large_areas={large_rectangular_areas}, "
                        f"peaks={significant_peaks}, bg_ratio={background_ratio:.2f}, "
                        f"structure={has_structure}, ratio={is_slide_ratio}")

            return is_ppt_content

        except Exception as e:
            logger.error(f"Failed to analyze PPT content in {image_path}: {e}")
            return True  # Default to including the image if analysis fails
    
    def filter_ppt_images(self, image_paths: List[Path],
                          progress_callback: Optional[callable] = None) -> List[Path]:
        """
        Filter images to keep only those that likely contain PPT content

        Args:
            image_paths: List of image file paths
            progress_callback: Optional callback function for progress updates (current, total)

        Returns:
            List of filtered image paths
        """
        logger.info(f"Filtering {len(image_paths)} images for PPT content")

        ppt_images = []
        progress = ProgressTracker(len(image_paths), "Filtering PPT content")

        for i, img_path in enumerate(image_paths):
            if self.detect_ppt_content(img_path):
                ppt_images.append(img_path)
            else:
                logger.debug(f"Filtered out non-PPT image: {img_path.name}")

            progress.update()

            # Call external progress callback if provided
            if progress_callback:
                progress_callback(i + 1, len(image_paths))

        filtered_count = len(image_paths) - len(ppt_images)
        logger.info(f"Filtered out {filtered_count} non-PPT images")
        logger.info(f"Remaining PPT images: {len(ppt_images)}")

        return ppt_images
    
    def process_images(self, image_paths: List[Path], 
                      output_dir: Path,
                      enhance: bool = True,
                      remove_duplicates: bool = True,
                      filter_ppt: bool = True) -> List[Path]:
        """
        Process a batch of images with all optimizations
        
        Args:
            image_paths: List of input image paths
            output_dir: Directory to save processed images
            enhance: Whether to enhance image quality
            remove_duplicates: Whether to remove duplicate images
            filter_ppt: Whether to filter for PPT content
            
        Returns:
            List of processed image paths
        """
        if not image_paths:
            return []
        
        logger.info(f"Processing {len(image_paths)} images")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        current_images = image_paths.copy()
        
        # Filter for PPT content first
        if filter_ppt:
            current_images = self.filter_ppt_images(current_images)
        
        # Remove duplicates
        if remove_duplicates:
            current_images = self.remove_duplicates(current_images)
        
        # Enhance images
        processed_images = []
        if enhance:
            progress = ProgressTracker(len(current_images), "Enhancing images")
            for i, img_path in enumerate(current_images):
                output_path = output_dir / f"processed_{i:06d}_{img_path.name}"
                enhanced_path = self.enhance_image(img_path, output_path)
                processed_images.append(enhanced_path)
                progress.update()
        else:
            processed_images = current_images
        
        logger.info(f"Image processing complete: {len(processed_images)} images ready")
        return processed_images
