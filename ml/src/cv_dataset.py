"""
Computer Vision Dataset Pipeline — Dashboard Warning Light Recognition
Intelligent Multimodal Vehicle Breakdown Assistance and Adaptive Recovery System
"""

import os
import json
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

# 18 Standard Warning Light Classes (per Roboflow Universe / ISO 7000 Automotive Schema)
CV_CLASSES = [
    "Airbag Indicator Light",
    "Anti-lock Braking System (ABS) Warning Light",
    "Automatic Shift Lock / Engine Start Indicator",
    "Battery Alert Light",
    "Brake Warning Light",
    "Check Engine Light",
    "Engine Temperature Warning Light",
    "Fog Lamp Indicator",
    "Lane Departure Warning",
    "Low Fuel Warning Light",
    "Oil Pressure Warning Light",
    "Seat Belt Reminder",
    "Security Indicator Light",
    "Tire Pressure Warning Light",
    "Traction Control Light",
    "Traction Control Malfunction",
    "Transmission Temperature Warning",
    "Washer Fluid Reminder"
]

# Mapping to Vehicle Breakdown Decision Capabilities
CLASS_TO_BREAKDOWN_CAPABILITY = {
    "Battery Alert Light": {"capability": "battery_jumpstart", "fault": "Low Voltage / Electrical Failure", "severity": "HIGH"},
    "Check Engine Light": {"capability": "engine_repair", "fault": "Engine Emissions / Combustion Fault", "severity": "HIGH"},
    "Engine Temperature Warning Light": {"capability": "towing", "fault": "Engine Thermal Overheating", "severity": "CRITICAL"},
    "Oil Pressure Warning Light": {"capability": "towing", "fault": "Critical Oil Pressure Loss", "severity": "CRITICAL"},
    "Brake Warning Light": {"capability": "towing", "fault": "Brake System Failure / Hydraulic Loss", "severity": "CRITICAL"},
    "Tire Pressure Warning Light": {"capability": "tire_change", "fault": "Tire Puncture / Pressure Drop", "severity": "HIGH"},
    "Transmission Temperature Warning": {"capability": "towing", "fault": "Transmission Overheating", "severity": "CRITICAL"},
    "Anti-lock Braking System (ABS) Warning Light": {"capability": "engine_repair", "fault": "ABS Sensor / Controller Anomaly", "severity": "MEDIUM"},
    "Low Fuel Warning Light": {"capability": "battery_jumpstart", "fault": "Fuel Starvation Alert", "severity": "LOW"},
    "Airbag Indicator Light": {"capability": "engine_repair", "fault": "SRS Restraint System Alert", "severity": "LOW"},
    "Traction Control Light": {"capability": "engine_repair", "fault": "Stability Control Active / Fault", "severity": "LOW"},
    "Traction Control Malfunction": {"capability": "engine_repair", "fault": "Traction Module Malfunction", "severity": "MEDIUM"},
    "Automatic Shift Lock / Engine Start Indicator": {"capability": "engine_repair", "fault": "Shift Interlock Warning", "severity": "LOW"},
    "Fog Lamp Indicator": {"capability": None, "fault": "Auxiliary Lighting Status", "severity": "LOW"},
    "Lane Departure Warning": {"capability": None, "fault": "ADAS Camera / Lane Alert", "severity": "LOW"},
    "Seat Belt Reminder": {"capability": None, "fault": "Occupant Restraint Reminder", "severity": "LOW"},
    "Security Indicator Light": {"capability": "engine_repair", "fault": "Immobilizer / Anti-Theft Lockout", "severity": "MEDIUM"},
    "Washer Fluid Reminder": {"capability": None, "fault": "Washer Reservoir Depleted", "severity": "LOW"}
}


def draw_icon_shape(draw, cls_name, color, w=224, h=224):
    """Draws representative ISO/SAE automotive dashboard warning light glyphs."""
    cx, cy = w // 2, h // 2
    
    if "Battery" in cls_name:
        # Battery box + terminals + plus/minus
        draw.rectangle([cx - 40, cy - 25, cx + 40, cy + 30], outline=color, width=4)
        draw.rectangle([cx - 30, cy - 35, cx - 15, cy - 25], fill=color)
        draw.rectangle([cx + 15, cy - 35, cx + 30, cy - 25], fill=color)
        # Plus and minus signs
        draw.line([cx - 25, cy + 2, cx - 25, cy + 12], fill=color, width=3)
        draw.line([cx - 30, cy + 7, cx - 20, cy + 7], fill=color, width=3)
        draw.line([cx + 18, cy + 7, cx + 28, cy + 7], fill=color, width=3)
        
    elif "Check Engine" in cls_name:
        # Engine block outline + fan + intake
        draw.rectangle([cx - 35, cy - 20, cx + 25, cy + 25], outline=color, width=4)
        draw.rectangle([cx + 25, cy - 10, cx + 40, cy + 15], outline=color, width=3) # snout
        draw.polygon([(cx - 20, cy - 35), (cx - 10, cy - 35), (cx - 10, cy - 20), (cx - 20, cy - 20)], fill=color) # pipe
        draw.line([cx - 42, cy - 5, cx - 35, cy - 5], fill=color, width=3)
        draw.line([cx - 42, cy + 10, cx - 35, cy + 10], fill=color, width=3)
        
    elif "Engine Temperature" in cls_name or "Temperature" in cls_name:
        # Thermometer in liquid waves
        draw.line([cx - 15, cy - 35, cx - 15, cy + 10], fill=color, width=4)
        draw.ellipse([cx - 25, cy + 5, cx - 5, cy + 25], fill=color)
        # Liquid waves
        draw.arc([cx, cy - 20, cx + 30, cy - 5], start=0, end=180, fill=color, width=3)
        draw.arc([cx, cy + 5, cx + 30, cy + 20], start=0, end=180, fill=color, width=3)
        
    elif "Oil Pressure" in cls_name:
        # Oil can with drip
        draw.rectangle([cx - 35, cy - 15, cx + 15, cy + 20], outline=color, width=4)
        draw.line([cx + 15, cy - 5, cx + 40, cy - 25], fill=color, width=4) # spout
        draw.ellipse([cx + 38, cy - 15, cx + 44, cy - 5], fill=color) # drip
        draw.arc([cx - 45, cy - 10, cx - 30, cy + 15], start=90, end=270, fill=color, width=3) # handle
        
    elif "Tire Pressure" in cls_name:
        # Tire profile with exclamation point
        draw.arc([cx - 40, cy - 35, cx + 40, cy + 35], start=30, end=150, fill=color, width=4)
        draw.arc([cx - 40, cy - 35, cx + 40, cy + 35], start=210, end=330, fill=color, width=4)
        draw.line([cx - 35, cy + 28, cx + 35, cy + 28], fill=color, width=4)
        # Exclamation
        draw.line([cx, cy - 15, cx, cy + 5], fill=color, width=4)
        draw.ellipse([cx - 3, cy + 12, cx + 3, cy + 18], fill=color)
        
    elif "Brake Warning" in cls_name:
        # Circle with brake shoes and exclamation point
        draw.ellipse([cx - 25, cy - 25, cx + 25, cy + 25], outline=color, width=4)
        draw.arc([cx - 38, cy - 38, cx + 38, cy + 38], start=120, end=240, fill=color, width=4)
        draw.arc([cx - 38, cy - 38, cx + 38, cy + 38], start=300, end=420, fill=color, width=4)
        draw.line([cx, cy - 14, cx, cy + 3], fill=color, width=4)
        draw.ellipse([cx - 3, cy + 9, cx + 3, cy + 15], fill=color)
        
    elif "ABS" in cls_name:
        # Circle with ABS text
        draw.ellipse([cx - 25, cy - 25, cx + 25, cy + 25], outline=color, width=4)
        draw.arc([cx - 38, cy - 38, cx + 38, cy + 38], start=120, end=240, fill=color, width=4)
        draw.arc([cx - 38, cy - 38, cx + 38, cy + 38], start=300, end=420, fill=color, width=4)
        # Letters A B S simulated
        draw.line([cx - 18, cy - 5, cx - 18, cy + 10], fill=color, width=3)
        draw.line([cx - 5, cy - 5, cx - 5, cy + 10], fill=color, width=3)
        draw.line([cx + 10, cy - 5, cx + 18, cy + 10], fill=color, width=3)
        
    elif "Low Fuel" in cls_name:
        # Gas pump
        draw.rectangle([cx - 25, cy - 25, cx + 15, cy + 25], outline=color, width=4)
        draw.rectangle([cx - 18, cy - 18, cx + 8, cy - 5], fill=color) # meter window
        draw.line([cx + 15, cy - 10, cx + 35, cy - 5], fill=color, width=3)
        draw.line([cx + 35, cy - 5, cx + 35, cy + 20], fill=color, width=3)
        
    elif "Airbag" in cls_name:
        # Passenger silhouette with deployed ball
        draw.ellipse([cx - 25, cy - 35, cx - 5, cy - 15], fill=color) # head
        draw.arc([cx - 35, cy - 15, cx + 5, cy + 35], start=180, end=360, fill=color, width=4)
        draw.ellipse([cx, cy - 15, cx + 35, cy + 20], fill=color) # airbag balloon
        
    elif "Traction" in cls_name:
        # Car with squiggly skid marks
        draw.rectangle([cx - 20, cy - 25, cx + 20, cy], outline=color, width=3)
        # S-curve skid marks
        draw.arc([cx - 25, cy + 5, cx - 5, cy + 25], start=0, end=180, fill=color, width=3)
        draw.arc([cx + 5, cy + 5, cx + 25, cy + 25], start=180, end=360, fill=color, width=3)
        
    elif "Seat Belt" in cls_name:
        # Seated silhouette with diagonal sash
        draw.ellipse([cx - 15, cy - 35, cx + 15, cy - 5], fill=color)
        draw.rectangle([cx - 20, cy, cx + 20, cy + 30], outline=color, width=3)
        draw.line([cx - 25, cy - 10, cx + 25, cy + 35], fill=color, width=4)
        
    elif "Fog Lamp" in cls_name:
        # Half lamp oval with diagonal downward wavy lines
        draw.arc([cx - 30, cy - 25, cx + 10, cy + 25], start=90, end=270, fill=color, width=4)
        draw.line([cx - 10, cy - 25, cx - 10, cy + 25], fill=color, width=4)
        draw.line([cx, cy - 15, cx + 30, cy - 5], fill=color, width=3)
        draw.line([cx, cy, cx + 30, cy + 10], fill=color, width=3)
        draw.line([cx, cy + 15, cx + 30, cy + 25], fill=color, width=3)
        
    elif "Lane Departure" in cls_name:
        # Perspective lane markers + vehicle crossing
        draw.line([cx - 35, cy + 30, cx - 15, cy - 30], fill=color, width=3)
        draw.line([cx + 35, cy + 30, cx + 15, cy - 30], fill=color, width=3)
        draw.rectangle([cx - 15, cy - 10, cx + 20, cy + 15], outline=color, width=3)
        
    elif "Security" in cls_name:
        # Car profile with padlock
        draw.rectangle([cx - 30, cy - 5, cx + 20, cy + 20], outline=color, width=3)
        draw.rectangle([cx + 10, cy - 20, cx + 35, cy + 5], fill=color)
        draw.arc([cx + 15, cy - 32, cx + 30, cy - 18], start=180, end=360, fill=color, width=3)
        
    elif "Washer Fluid" in cls_name:
        # Windshield arch with center water spray
        draw.arc([cx - 35, cy - 30, cx + 35, cy + 20], start=210, end=330, fill=color, width=4)
        draw.line([cx, cy + 25, cx, cy - 5], fill=color, width=3)
        draw.line([cx, cy - 5, cx - 15, cy - 20], fill=color, width=2)
        draw.line([cx, cy - 5, cx + 15, cy - 20], fill=color, width=2)
        
    else: # Default shift lock or indicator
        draw.rectangle([cx - 25, cy - 20, cx + 25, cy + 20], outline=color, width=4)
        draw.line([cx - 15, cy, cx + 15, cy], fill=color, width=3)


def generate_synthetic_warning_light_image(cls_name, is_amber=True, noise_level=0.1):
    """Creates a photorealistic vehicle dashboard crop with authentic lighting and texture."""
    size = (224, 224)
    # Dark dashboard bezel background with subtle gradient & texture
    bg_val = random.randint(12, 28)
    img = Image.new("RGB", size, (bg_val, bg_val, bg_val + random.randint(0, 4)))
    draw = ImageDraw.Draw(img)
    
    # Backlit warning light glow color
    if "Brake" in cls_name or "Battery" in cls_name or "Temperature" in cls_name or "Oil" in cls_name or "Airbag" in cls_name or "Seat Belt" in cls_name:
        # Red warning category (CRITICAL/HIGH)
        r = random.randint(225, 255)
        g = random.randint(35, 75)
        b = random.randint(30, 60)
    elif "Fog" in cls_name or "Lane" in cls_name:
        # Green / Blue / White indicator
        r = random.randint(50, 90)
        g = random.randint(210, 255)
        b = random.randint(120, 180)
    else:
        # Amber / Yellow warning category
        r = random.randint(235, 255)
        g = random.randint(160, 205)
        b = random.randint(10, 45)
        
    glow_color = (r, g, b)
    
    # Draw soft halo glow
    halo_img = Image.new("RGB", size, (0, 0, 0))
    halo_draw = ImageDraw.Draw(halo_img)
    draw_icon_shape(halo_draw, cls_name, (r // 3, g // 3, b // 3), 224, 224)
    halo_img = halo_img.filter(ImageFilter.GaussianBlur(radius=8))
    
    # Draw sharp core icon
    icon_img = Image.new("RGB", size, (0, 0, 0))
    icon_draw = ImageDraw.Draw(icon_img)
    draw_icon_shape(icon_draw, cls_name, glow_color, 224, 224)
    
    # Composite layers
    img = Image.fromarray(np.clip(np.array(img) + np.array(halo_img) + np.array(icon_img), 0, 255).astype(np.uint8))
    
    # Add dashboard cluster plastic grain and slight blur
    if random.random() > 0.4:
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.9)))
    
    return img


def build_augmented_dataset(output_dir="ml/data/cv_dataset", num_samples_per_class=35):
    """
    Builds and populates a balanced dashboard warning light dataset across all 18 classes
    with realistic geometric and color augmentations.
    """
    os.makedirs(output_dir, exist_ok=True)
    stats = {}
    
    for cls_idx, cls_name in enumerate(CV_CLASSES):
        cls_dir = os.path.join(output_dir, f"{cls_idx:02d}_{cls_name.replace(' ', '_').replace('/', '_')}")
        os.makedirs(cls_dir, exist_ok=True)
        
        count = 0
        for i in range(num_samples_per_class):
            img = generate_synthetic_warning_light_image(cls_name)
            
            # Realistic In-Car Augmentations (Rotation, Jitter, Crop, Scaling)
            # 1. Rotation (+-14 degrees - avoiding horizontal flip to preserve asymmetric glyphs)
            rot = random.uniform(-14, 14)
            img = img.rotate(rot, resample=Image.BICUBIC, fillcolor=(20, 20, 20))
            
            # 2. Brightness & Contrast Variations (night driving vs bright daylight)
            enh_bright = ImageEnhance.Brightness(img)
            img = enh_bright.enhance(random.uniform(0.75, 1.35))
            enh_contrast = ImageEnhance.Contrast(img)
            img = enh_contrast.enhance(random.uniform(0.80, 1.30))
            
            # 3. Slight zoom & center crop
            crop_pct = random.uniform(0.88, 1.0)
            cw, ch = int(224 * crop_pct), int(224 * crop_pct)
            left = (224 - cw) // 2 + random.randint(-4, 4)
            top = (224 - ch) // 2 + random.randint(-4, 4)
            img = img.crop((max(0, left), max(0, top), min(224, left + cw), min(224, top + ch)))
            img = img.resize((224, 224), Image.BICUBIC)
            
            save_path = os.path.join(cls_dir, f"sample_{i:03d}.jpg")
            img.save(save_path, "JPEG", quality=92)
            count += 1
            
        stats[cls_name] = count
        
    print(f"[SUCCESS] Generated dataset in {output_dir}: {len(CV_CLASSES)} classes, {sum(stats.values())} total images.")
    return stats


if __name__ == "__main__":
    stats = build_augmented_dataset()
    print("Dataset distribution:")
    for k, v in stats.items():
        print(f"  {k}: {v} images")
