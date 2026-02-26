import os
from PIL import Image

assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "assets")
webp_path = os.path.join(assets_dir, "edenred-minilogo.webp")
png_path = os.path.join(assets_dir, "edenred-minilogo.png")

if os.path.exists(webp_path):
    # Convert webp to png
    img = Image.open(webp_path)
    img.save(png_path, "PNG")
else:
    pass
