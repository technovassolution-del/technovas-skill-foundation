import pandas as pd
import qrcode
import os

# Excel file
excel_file = "student_admissions.xlsx"

# Output folder
output_folder = "QR_Codes"
os.makedirs(output_folder, exist_ok=True)

# Read Excel
df = pd.read_excel(excel_file)

# Generate QR codes
for _, row in df.iterrows():

    enrollment_no = row["Enrollment No"]
    qr_token = row["QR Token"]

    # Skip empty values
    if pd.isna(enrollment_no) or pd.isna(qr_token):
        continue

    # Generate QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )

    qr.add_data(str(qr_token).strip())
    qr.make(fit=True)

    img = qr.make_image()

    # Filename = Enrollment No
    filename = f"{enrollment_no}.png"

    # Save
    filepath = os.path.join(output_folder, filename)
    img.save(filepath)

    print(f"Created: {filepath}")

print("All QR codes generated successfully!")