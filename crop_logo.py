from PIL import Image, ImageChops

def trim_and_crop():
    image_path = r"c:\Users\vvign\OneDrive\Documents\Desktop\Projects\Project-QAML\quantum-drug-repurposing\frontend\public\logo.png"
    img = Image.open(image_path).convert("RGBA")
    
    # 1. Trim background (find bounding box of non-white/non-transparent pixels)
    # Background in the image is #f0f2f5 or similar (very light grey/white)
    # We'll treat anything very light as background
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    diff = ImageChops.difference(img, bg)
    # Thresholding to ignore slight noise
    diff = diff.convert("L")
    bbox = diff.getbbox()
    
    if not bbox:
        print("Could not find logo in image.")
        return

    # 2. Extract just the shield portion. 
    # Based on the original image, the shield is the top part.
    # The text "QAML" starts below it.
    # We'll analyze the horizontal density to find the gap.
    
    trimmed = img.crop(bbox)
    width, height = trimmed.size
    
    # Horizontal projection (average brightness per row)
    # Or just count non-background pixels per row
    mask = trimmed.convert("L").point(lambda x: 0 if x > 240 else 255, '1')
    rows = []
    for y in range(height):
        row_sum = 0
        for x in range(width):
            if mask.getpixel((x, y)):
                row_sum += 1
        rows.append(row_sum)
        
    # Find the first major gap from top to bottom
    # The shield is one solid block, then there's a small gap, then "QAML"
    shield_end = height
    gap_threshold = width * 0.01 # 1% of width
    
    # Start looking for gap after finding some content (the shield)
    content_started = False
    for y in range(height):
        if rows[y] > gap_threshold:
            content_started = True
        elif content_started and rows[y] <= gap_threshold:
            # We found a gap after the shield
            # Look ahead a few pixels to ensure it's a real gap and not just a thin line in the logo
            is_real_gap = True
            for next_y in range(y, min(y + 10, height)):
                if rows[next_y] > gap_threshold:
                    is_real_gap = False
                    break
            if is_real_gap:
                shield_end = y
                break
                
    # Crop the shield
    shield_img = trimmed.crop((0, 0, width, shield_end))
    
    # Final trim of the shield itself (in case of extra horizontal space)
    shield_bbox = shield_img.convert("L").point(lambda x: 0 if x > 240 else 255, '1').getbbox()
    if shield_bbox:
        shield_img = shield_img.crop(shield_bbox)
        
    # Add a small margin (e.g. 5%)
    w, h = shield_img.size
    margin = int(min(w, h) * 0.05)
    final_img = Image.new("RGBA", (w + 2*margin, h + 2*margin), (255, 255, 255, 0))
    final_img.paste(shield_img, (margin, margin))
    
    # Save back to same location
    final_img.save(image_path)
    print(f"Successfully cropped and saved logo to {image_path}")

if __name__ == "__main__":
    trim_and_crop()
