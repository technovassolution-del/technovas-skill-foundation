import cv2
import mssql_python
import numpy as np
import face_recognition


# =========================================================
# SQL SERVER CONNECTION
# Windows Authentication
# =========================================================

def get_connection():

    return mssql_python.connect(
        "Server=DESKTOP-B4RCPPB\\SQLEXPRESS;"
        "Database=technovas_masterdb;"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )


# =========================================================
# SAVE EMPLOYEE
# =========================================================

def save_employee(
    employee_code,
    photo_bytes,
    embedding
):

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        # ---------------------------------------------
        # Convert embedding to float32
        # ---------------------------------------------

        embedding_array = np.asarray(
            embedding,
            dtype=np.float32
        )

        # ---------------------------------------------
        # Convert embedding to bytes
        # ---------------------------------------------

        embedding_bytes = embedding_array.tobytes()

        # ---------------------------------------------
        # INSERT
        # IMPORTANT:
        # mssql-python uses ?
        # NOT %s
        # ---------------------------------------------

        sql = """
            INSERT INTO Employees
            (
                EmployeeCode,
                Photo,
                Embedding,
                EmbeddingSize
            )
            VALUES
            (?, ?, ?, ?, ?)
        """

        cursor.execute(
            sql,
            (
                employee_code,
                photo_bytes,
                embedding_bytes,
                len(embedding_array)
            )
        )

        conn.commit()

        print("Employee saved successfully!")

    except Exception as e:

        if conn:
            conn.rollback()

        print("Database error:")
        print(type(e).__name__)
        print(str(e))

        raise

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# CAPTURE PHOTO
# =========================================================

def capture_employee(
    employee_code
    
):

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():

        print("Camera could not be opened.")

        return


    print()
    print("======================================")
    print("       FACE CAPTURE")
    print("======================================")
    print("Look at the camera.")
    print("Press SPACE to capture.")
    print("Press ESC to cancel.")
    print("======================================")


    captured_frame = None


    # =====================================================
    # CAMERA LOOP
    # =====================================================

    while True:

        ret, frame = camera.read()

        if not ret:

            print("Could not read camera.")

            break


        # Mirror camera

        frame = cv2.flip(
            frame,
            1
        )


        # Instructions

        cv2.putText(
            frame,
            "SPACE = Capture | ESC = Exit",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )


        cv2.imshow(
            "Employee Face Registration",
            frame
        )


        key = cv2.waitKey(1) & 0xFF


        # SPACE

        if key == 32:

            captured_frame = frame.copy()

            break


        # ESC

        elif key == 27:

            camera.release()

            cv2.destroyAllWindows()

            print("Capture cancelled.")

            return


    camera.release()

    cv2.destroyAllWindows()


    if captured_frame is None:

        return


    # =====================================================
    # FACE DETECTION
    # =====================================================

    rgb_image = cv2.cvtColor(
        captured_frame,
        cv2.COLOR_BGR2RGB
    )


    face_locations = face_recognition.face_locations(
        rgb_image
    )


    if len(face_locations) == 0:

        print("No face detected.")

        return


    if len(face_locations) > 1:

        print(
            "Multiple faces detected."
        )

        print(
            "Please capture only one person."
        )

        return


    print(
        "Face detected successfully."
    )


    # =====================================================
    # GENERATE FACE EMBEDDING
    # =====================================================

    encodings = face_recognition.face_encodings(
        rgb_image,
        face_locations
    )


    if len(encodings) == 0:

        print(
            "Could not generate face embedding."
        )

        return


    embedding = encodings[0]


    print(
        "Embedding generated."
    )

    print(
        "Embedding dimensions:",
        len(embedding)
    )


    # =====================================================
    # CONVERT PHOTO TO JPEG BYTES
    # =====================================================

    success, buffer = cv2.imencode(
        ".jpg",
        captured_frame
    )


    if not success:

        print(
            "Could not convert photo."
        )

        return


    photo_bytes = buffer.tobytes()


    print(
        "Photo converted to bytes."
    )


    # =====================================================
    # SAVE PHOTO + EMBEDDING
    # =====================================================

    save_employee(
        employee_code,
        photo_bytes,
        embedding
    )


    # =====================================================
    # SUCCESS
    # =====================================================

    print()
    print("======================================")
    print("             SUCCESS")
    print("======================================")
    print(
        "Employee:",
        employee_name
    )
    print(
        "Code:",
        employee_code
    )
    print(
        "Embedding Size:",
        len(embedding)
    )
    print(
        "Photo Size:",
        len(photo_bytes),
        "bytes"
    )
    print(
        "Photo + Embedding saved to SQL Server."
    )
    print("======================================")


# =========================================================
# MAIN
# =========================================================


    