import base64

import cv2
import numpy as np
import face_recognition


# --------------------------------------------------
# BASE64 IMAGE → BYTES
# --------------------------------------------------

def base64_to_bytes(image_data):

    if not image_data:
        raise ValueError("Image data is required")

    if "," in image_data:
        image_data = image_data.split(",", 1)[1]

    try:

        return base64.b64decode(image_data)

    except Exception as e:

        raise ValueError("Invalid Base64 image") from e


# --------------------------------------------------
# BASE64 IMAGE → OPENCV IMAGE
# --------------------------------------------------

def base64_to_image(image_data):

    image_bytes = base64_to_bytes(
        image_data
    )

    np_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8
    )

    image = cv2.imdecode(
        np_array,
        cv2.IMREAD_COLOR
    )

    if image is None:

        raise ValueError(
            "Unable to decode image"
        )

    return image


# --------------------------------------------------
# IMAGE → FACE ENCODING
# --------------------------------------------------

def get_face_encoding(image):

    if image is None:

        raise ValueError(
            "Invalid image"
        )

    rgb_image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    face_locations = face_recognition.face_locations(
        rgb_image,
        model="hog"
    )

    if len(face_locations) == 0:

        raise ValueError(
            "No face detected. Please capture a clear photo."
        )

    if len(face_locations) > 1:

        raise ValueError(
            "Multiple faces detected. Please capture only one face."
        )

    encodings = face_recognition.face_encodings(
        rgb_image,
        face_locations
    )

    if not encodings:

        raise ValueError(
            "Unable to generate face encoding"
        )

    return encodings[0]


# --------------------------------------------------
# ENCODING → BYTES
# --------------------------------------------------

def encoding_to_bytes(encoding):

    return np.asarray(
        encoding,
        dtype=np.float64
    ).tobytes()


# --------------------------------------------------
# BYTES → ENCODING
# --------------------------------------------------

def bytes_to_encoding(encoding_bytes):

    if not encoding_bytes:

        raise ValueError(
            "Face encoding is empty"
        )

    return np.frombuffer(
        encoding_bytes,
        dtype=np.float64
    )


# --------------------------------------------------
# COMPARE TWO FACES
# --------------------------------------------------

def compare_faces(
    known_encoding,
    unknown_encoding,
    tolerance=0.50
):

    distance = face_recognition.face_distance(
        [known_encoding],
        unknown_encoding
    )[0]

    is_match = distance <= tolerance

    confidence = max(
        0.0,
        min(
            100.0,
            (1.0 - distance) * 100
        )
    )

    return is_match, float(confidence)