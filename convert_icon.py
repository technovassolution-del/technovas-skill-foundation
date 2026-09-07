from PIL import Image

img = Image.open("icons8-attendance-100.png")

# Convert to RGBA
img = img.convert("RGBA")

# Create a proper Windows ICO with multiple sizes
img.save(
    "attendance.ico",
    format="ICO",
    sizes=[
        (16, 16),
        (24, 24),
        (32, 32),
        (48, 48),
        (64, 64),
        (128, 128),
        (256, 256),
    ],
)

print("attendance.ico created successfully")