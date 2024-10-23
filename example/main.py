import os
import sys
import pygame
import threading
import random
import math
from PIL import Image, ImageEnhance, ImageFilter
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

"""
Image Viewer Program

This program allows users to view images in a folder, navigate through them,
move or copy images to numbered subfolders, and delete images.

Usage:
    python main.py [folder_path]

If no folder_path is provided, the current working directory is used.
"""

from multiprocessing import Pool, cpu_count

def validate_image(path):
    """Validate if a file is a readable image."""
    try:
        with Image.open(path) as img:
            img.verify()
        return path
    except:
        return None

def load_images(folder):
    """
    Load all supported image files from the specified folder using parallel processing.

    Args:
        folder (str): Path to the folder containing images.

    Returns:
        list: A list of full paths to valid image files.
    """
    if not os.path.exists(folder):
        print(f"Error: Folder '{folder}' does not exist!")
        return []
        
    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a directory!")
        return []

    supported_formats = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
    
    try:
        files = os.listdir(folder)
        if not files:
            print(f"The folder '{folder}' is empty!")
            return []
            
        # Get potential image paths
        image_paths = [
            os.path.join(folder, f) for f in files 
            if f.lower().endswith(supported_formats)
        ]
        
        if not image_paths:
            print(f"No supported images found in '{folder}'")
            print(f"Supported formats: {', '.join(supported_formats)}")
            return []
            
        # Validate images in parallel
        with Pool(processes=cpu_count()) as pool:
            valid_images = pool.map(validate_image, image_paths)
            
        # Filter out None results (invalid images)
        images = [img for img in valid_images if img is not None]
        
        if not images:
            print("No valid images found in folder")
            
        return images
        
    except PermissionError:
        print(f"Error: No permission to access folder '{folder}'")
        return []
    except Exception as e:
        print(f"Error accessing folder '{folder}': {e}")
        return []

def move_or_copy_image(src, dst, mode='move'):
    """
    Move or copy an image file to a destination.

    Args:
        src (str): Source path of the image file.
        dst (str): Destination path for the image file.
        mode (str): 'move' to move the file, 'copy' to copy it.

    Raises:
        OSError: If there's an error during the file operation.
    """
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if mode == 'move':
            os.rename(src, dst)
        else:
            import shutil
            shutil.copy2(src, dst)
    except OSError as e:
        print(f"Error during file operation: {e}")

class ImageCache:
    def __init__(self, max_memory_mb=500):
        self.cache = {}
        self.access_order = deque()
        self.max_memory = max_memory_mb * 1024 * 1024  # Convert MB to bytes
        self.current_memory = 0
        
    def _get_surface_size(self, surface):
        """Estimate memory usage of a pygame surface in bytes"""
        return surface.get_width() * surface.get_height() * 4  # 4 bytes per pixel (32-bit)
        
    def get(self, path):
        if path in self.cache:
            self.access_order.remove(path)
            self.access_order.append(path)
            return self.cache[path]
        return None
        
    def put(self, path, surface):
        if not surface:
            return
            
        surface_size = self._get_surface_size(surface)
        
        # Remove old entries if adding this would exceed memory limit
        while self.current_memory + surface_size > self.max_memory and self.access_order:
            oldest = self.access_order.popleft()
            if oldest in self.cache:
                old_surface = self.cache[oldest]
                self.current_memory -= self._get_surface_size(old_surface)
                del self.cache[oldest]
                
        # Add new surface
        if path in self.cache:
            self.access_order.remove(path)
            old_surface = self.cache[path]
            self.current_memory -= self._get_surface_size(old_surface)
            
        self.cache[path] = surface
        self.current_memory += surface_size
        self.access_order.append(path)

def apply_random_effect(image):
    """Apply a random artistic effect to the image."""
    effects = [
        lambda img: img.filter(ImageFilter.EDGE_ENHANCE),
        lambda img: img.filter(ImageFilter.CONTOUR),
        lambda img: img.filter(ImageFilter.EMBOSS),
        lambda img: ImageEnhance.Color(img).enhance(random.uniform(0.0, 2.0)),
        lambda img: img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 2.0))),
        lambda img: img.rotate(random.randint(-10, 10), expand=True),
    ]
    return random.choice(effects)(image)

def load_image_to_surface(image_path, art_mode=False, thumbnail_size=None):
    """Load an image file into a pygame surface with optional artistic effects."""
    try:
        image = Image.open(image_path)
        image = image.convert('RGB')
        if art_mode:
            image = apply_random_effect(image)
        if thumbnail_size:
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
        return pygame.image.fromstring(image.tobytes(), image.size, image.mode)
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

def display_image(screen, image_path, cache, zoom=1.0, pan_x=0, pan_y=0, art_mode=False):
    """
    Display an image on the screen using caching with zoom and pan support.

    Args:
        screen (pygame.Surface): The pygame screen surface.
        image_path (str): Path to the image file.
        cache (ImageCache): Cache for loaded images.
        zoom (float): Zoom level (1.0 = 100%)
        pan_x (int): Horizontal pan offset
        pan_y (int): Vertical pan offset
        art_mode (bool): Whether to apply artistic effects
    """
    try:
        # Try to get from cache first
        surface = cache.get(image_path)
        if surface is None:
            surface = load_image_to_surface(image_path, art_mode)
            if surface is None:
                return False
            cache.put(image_path, surface)
            
        screen.fill((0, 0, 0))
        screen_rect = screen.get_rect()
        
        # Calculate zoomed size
        new_width = int(surface.get_width() * zoom)
        new_height = int(surface.get_height() * zoom)
        if zoom != 1.0:
            scaled_surface = pygame.transform.smoothscale(surface, (new_width, new_height))
        else:
            scaled_surface = surface
            
        # Calculate centered position with pan
        image_rect = scaled_surface.get_rect()
        image_rect.center = screen_rect.center
        image_rect.x += pan_x
        image_rect.y += pan_y
        
        screen.blit(scaled_surface, image_rect)
        pygame.display.flip()
        return True
    except Exception as e:
        print(f"Error displaying image: {e}")
        return False

class ImagePreloader:
    def __init__(self, max_workers=2):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.preload_queue = set()
        
    def preload_images(self, images, current_index, cache, num_ahead=2, num_behind=1):
        """Preload upcoming and previous images in background."""
        if not images:
            return
            
        # Calculate indices to preload
        indices = []
        # Add upcoming images
        for i in range(1, num_ahead + 1):
            indices.append((current_index + i) % len(images))
        # Add previous images
        for i in range(1, num_behind + 1):
            indices.append((current_index - i) % len(images))
            
        # Submit preload tasks for uncached images
        for idx in indices:
            path = images[idx]
            if path not in self.preload_queue and not cache.get(path):
                self.preload_queue.add(path)
                self.executor.submit(self._preload_task, path, cache)
                
    def _preload_task(self, path, cache):
        """Background task to load an image into cache."""
        try:
            surface = load_image_to_surface(path)
            if surface:
                cache.put(path, surface)
        finally:
            self.preload_queue.discard(path)

def save_contact_sheet(images, output_path=None):
    """Create and save a contact sheet of all images"""
    if not images:
        return False
        
    # Default output path if none provided
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"contact_sheet_{timestamp}.jpg"
    
    # Calculate grid dimensions
    num_images = len(images)
    grid_size = math.ceil(math.sqrt(num_images))
    
    # Create blank contact sheet
    thumb_size = (200, 200)  # Size of each thumbnail
    sheet_size = (grid_size * thumb_size[0], grid_size * thumb_size[1])
    contact_sheet = Image.new('RGB', sheet_size, (0, 0, 0))
    
    # Add each image
    for i, img_path in enumerate(images):
        try:
            # Load and resize image
            img = Image.open(img_path)
            img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
            
            # Calculate position
            row = i // grid_size
            col = i % grid_size
            x = col * thumb_size[0]
            y = row * thumb_size[1]
            
            # Center image in its cell
            x_offset = (thumb_size[0] - img.width) // 2
            y_offset = (thumb_size[1] - img.height) // 2
            
            # Paste into contact sheet
            contact_sheet.paste(img, (x + x_offset, y + y_offset))
            
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            continue
    
    # Save contact sheet
    try:
        contact_sheet.save(output_path, quality=95)
        print(f"Contact sheet saved as: {output_path}")
        return True
    except Exception as e:
        print(f"Error saving contact sheet: {e}")
        return False

def create_mosaic(screen, images, cache):
    """Create a mosaic view of all images"""
    if not images:
        return False
        
    screen_rect = screen.get_rect()
    num_images = len(images)
    
    # Calculate grid dimensions
    grid_size = math.ceil(math.sqrt(num_images))
    cell_width = screen_rect.width // grid_size
    cell_height = screen_rect.height // grid_size
    
    # Clear screen
    screen.fill((0, 0, 0))
    
    # Load and display thumbnails
    for i, img_path in enumerate(images):
        row = i // grid_size
        col = i % grid_size
        
        # Calculate position
        x = col * cell_width
        y = row * cell_height
        
        # Load thumbnail
        surface = cache.get(f"thumb_{img_path}")
        if surface is None:
            surface = load_image_to_surface(img_path, thumbnail_size=(cell_width, cell_height))
            if surface:
                cache.put(f"thumb_{img_path}", surface)
        
        if surface:
            # Scale to fit cell
            scaled = pygame.transform.smoothscale(surface, (cell_width-4, cell_height-4))
            screen.blit(scaled, (x+2, y+2))
    
    pygame.display.flip()
    return True

def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Image Viewer")

    folder = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    images = load_images(folder)
    
    if not images:
        print("No images found in the specified folder.")
        return

    current_index = 0
    running = True
    mode = 'move'
    cache = ImageCache(max_memory_mb=500)  # Limit cache to 500MB
    preloader = ImagePreloader(max_workers=2)
    zoom = 1.0
    pan_x = 0
    pan_y = 0
    slideshow_active = False
    slideshow_delay = 3000  # milliseconds
    last_slide_time = pygame.time.get_ticks()
    art_mode = False
    mosaic_mode = False

    while running:
        if mosaic_mode:
            if not create_mosaic(screen, images, cache):
                running = False
                continue
        elif not display_image(screen, images[current_index], cache, zoom, pan_x, pan_y, art_mode):
            # Remove invalid image and continue
            images.pop(current_index)
            if not images:
                running = False
                continue
            current_index %= len(images)
            continue
            
        # Preload images in background
        preloader.preload_images(images, current_index, cache)

        # Handle slideshow
        if slideshow_active:
            current_time = pygame.time.get_ticks()
            if current_time - last_slide_time > slideshow_delay:
                current_index = (current_index + 1) % len(images)
                last_slide_time = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Mouse wheel up
                    zoom = min(4.0, zoom * 1.1)
                elif event.button == 5:  # Mouse wheel down
                    zoom = max(0.1, zoom / 1.1)
            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[0]:  # Left mouse button
                    pan_x += event.rel[0]
                    pan_y += event.rel[1]
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Reset zoom and pan
                    zoom = 1.0
                    pan_x = 0
                    pan_y = 0
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_RIGHT:
                    current_index = (current_index + 1) % len(images)
                elif event.key == pygame.K_LEFT:
                    current_index = (current_index - 1) % len(images)
                elif event.key == pygame.K_h:
                    print("Help: Arrow keys to navigate, 1-9 to move/copy, Delete to delete, Space for slideshow")
                    print("A to toggle art mode, M to toggle mosaic view, C to save contact sheet")
                    print("R to reset view, Q to quit")
                elif event.key == pygame.K_c:
                    if save_contact_sheet(images):
                        print("Contact sheet saved successfully!")
                elif event.key == pygame.K_m:
                    mosaic_mode = not mosaic_mode
                    print(f"Mosaic view: {'On' if mosaic_mode else 'Off'}")
                elif event.key == pygame.K_a:
                    art_mode = not art_mode
                    cache.cache.clear()  # Clear cache to force reload with new effects
                    print(f"Art mode: {'On' if art_mode else 'Off'}")
                elif event.key == pygame.K_SPACE:
                    slideshow_active = not slideshow_active
                    print(f"Slideshow: {'On' if slideshow_active else 'Off'}")
                elif event.key == pygame.K_DELETE:
                    os.remove(images[current_index])
                    images.pop(current_index)
                    if not images:
                        running = False
                    else:
                        current_index %= len(images)
                elif event.key in range(pygame.K_1, pygame.K_9 + 1):
                    subfolder = str(event.key - pygame.K_0)
                    dst = os.path.join(folder, subfolder, os.path.basename(images[current_index]))
                    move_or_copy_image(images[current_index], dst, mode)
                    if mode == 'move':
                        images.pop(current_index)
                        if not images:
                            running = False
                        else:
                            current_index %= len(images)
                elif event.key == pygame.K_CAPSLOCK:
                    mode = 'copy' if mode == 'move' else 'move'
                    print(f"Mode changed to: {mode.upper()}")

    pygame.quit()

if __name__ == "__main__":
    main()
