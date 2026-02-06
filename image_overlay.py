"""
Image overlay module for MapToPoster
Handles badge/logo placement on maps
"""
import os
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import numpy as np


def add_badge_overlay(ax, badge_path, position, size=0.15, alpha=0.9, glow=True):
    """
    Add a team badge overlay to the map
    
    Args:
        ax: Matplotlib axes object
        badge_path: Path to badge PNG file
        position: (lat, lon) tuple OR (x, y) in axes coordinates
        size: Size as fraction of plot (0.0-1.0)
        alpha: Transparency (0.0-1.0)
        glow: Add glow effect around badge
        
    Returns:
        AnnotationBbox object
    """
    if not os.path.exists(badge_path):
        print(f"⚠️  Badge file not found: {badge_path}")
        return None
    
    try:
        # Load badge image
        badge_img = Image.open(badge_path)
        
        # Ensure RGBA mode
        if badge_img.mode != 'RGBA':
            badge_img = badge_img.convert('RGBA')
        
        # Resize badge
        aspect_ratio = badge_img.width / badge_img.height
        new_width = int(size * 1000)  # Base size
        new_height = int(new_width / aspect_ratio)
        badge_img = badge_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Apply alpha
        if alpha < 1.0:
            badge_array = np.array(badge_img)
            badge_array[:, :, 3] = (badge_array[:, :, 3] * alpha).astype(np.uint8)
            badge_img = Image.fromarray(badge_array)
        
        # Create OffsetImage
        imagebox = OffsetImage(badge_img, zoom=1.0)
        
        # Create annotation
        # If position is (lat, lon), convert to data coordinates
        # If position is already in axes coords (0-1), use directly
        if isinstance(position, tuple) and len(position) == 2:
            # Assume axes coordinates (0-1 range)
            xy = position
            xycoords = 'axes fraction'
        else:
            xy = position
            xycoords = 'data'
        
        ab = AnnotationBbox(
            imagebox, 
            xy,
            xycoords=xycoords,
            frameon=False,
            box_alignment=(0.5, 0.5)
        )
        
        # Add glow effect if requested
        if glow:
            # Create a white circle behind the badge
            circle = patches.Circle(
                xy, 
                size * 0.08,  # Slightly larger than badge
                transform=ax.transAxes,
                facecolor='white',
                edgecolor='none',
                alpha=0.3,
                zorder=9
            )
            ax.add_patch(circle)
        
        # Add badge
        ax.add_artist(ab)
        
        return ab
        
    except Exception as e:
        print(f"✗ Error adding badge overlay: {e}")
        return None


def add_stadium_marker(ax, coords, color='red', size=200, alpha=0.8, style='star'):
    """
    Add a marker at stadium location
    
    Args:
        ax: Matplotlib axes object
        coords: (lat, lon) tuple in axes coordinates (0-1)
        color: Marker color
        size: Marker size
        alpha: Transparency
        style: 'star', 'circle', 'pin', or 'crosshair'
    """
    x, y = coords
    
    if style == 'star':
        ax.scatter(x, y, 
                  marker='*', 
                  s=size, 
                  c=color, 
                  alpha=alpha,
                  edgecolors='white',
                  linewidths=2,
                  transform=ax.transAxes,
                  zorder=12)
    elif style == 'circle':
        circle = patches.Circle(
            (x, y),
            0.02,  # Radius in axes coordinates
            transform=ax.transAxes,
            facecolor=color,
            edgecolor='white',
            linewidth=2,
            alpha=alpha,
            zorder=12
        )
        ax.add_patch(circle)
    elif style == 'pin':
        # Map pin shape (triangle pointing down with circle on top)
        ax.scatter(x, y, 
                  marker='v',  # Triangle down
                  s=size, 
                  c=color, 
                  alpha=alpha,
                  edgecolors='white',
                  linewidths=2,
                  transform=ax.transAxes,
                  zorder=12)
        ax.scatter(x, y + 0.015,  # Circle above
                  marker='o', 
                  s=size * 0.4, 
                  c=color, 
                  alpha=alpha,
                  edgecolors='white',
                  linewidths=2,
                  transform=ax.transAxes,
                  zorder=12)
    elif style == 'crosshair':
        # Crosshair
        line_length = 0.03
        ax.plot([x - line_length, x + line_length], [y, y],
               color=color, linewidth=3, alpha=alpha,
               transform=ax.transAxes, zorder=12)
        ax.plot([x, x], [y - line_length, y + line_length],
               color=color, linewidth=3, alpha=alpha,
               transform=ax.transAxes, zorder=12)
        # Center dot
        ax.scatter(x, y, 
                  marker='o', 
                  s=size * 0.3, 
                  c=color, 
                  alpha=alpha,
                  edgecolors='white',
                  linewidths=2,
                  transform=ax.transAxes,
                  zorder=12)


def calculate_axes_position(lat, lon, map_bounds):
    """
    Convert lat/lon to axes coordinates (0-1 range)
    
    Args:
        lat: Latitude
        lon: Longitude
        map_bounds: (min_lat, max_lat, min_lon, max_lon) tuple
        
    Returns:
        (x, y) in axes coordinates
    """
    min_lat, max_lat, min_lon, max_lon = map_bounds
    
    # Normalize to 0-1 range
    x = (lon - min_lon) / (max_lon - min_lon) if max_lon != min_lon else 0.5
    y = (lat - min_lat) / (max_lat - min_lat) if max_lat != min_lat else 0.5
    
    return (x, y)


def create_circular_badge_mask(image_path, output_path=None):
    """
    Create a circular mask for a badge image
    
    Args:
        image_path: Path to input image
        output_path: Path to save masked image (optional)
        
    Returns:
        PIL Image object
    """
    img = Image.open(image_path).convert('RGBA')
    
    # Create circular mask
    size = min(img.size)
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    
    # Crop to square
    if img.size[0] != img.size[1]:
        # Center crop to square
        left = (img.size[0] - size) // 2
        top = (img.size[1] - size) // 2
        img = img.crop((left, top, left + size, top + size))
    
    # Apply mask
    output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0))
    output.putalpha(mask)
    
    if output_path:
        output.save(output_path)
    
    return output
