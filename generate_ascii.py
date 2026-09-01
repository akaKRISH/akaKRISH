import cv2
import numpy as np

def generate_ascii(image_path, width=40):
    chars = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return "ERROR: Could not load image"
        
        # calculate ratio
        height, old_width = img.shape
        ratio = height / old_width
        new_height = int(width * ratio * 0.5) # text characters are taller than wide
        
        resized = cv2.resize(img, (width, new_height))
        
        ascii_img = ""
        for row in resized:
            for pixel in row:
                ascii_img += chars[pixel // 25]
            ascii_img += "\n"
        return ascii_img
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    ascii_art = generate_ascii("assets/avatar/profile.png", width=45)
    with open("assets/ascii/pfp.txt", "w") as f:
        f.write(ascii_art)
