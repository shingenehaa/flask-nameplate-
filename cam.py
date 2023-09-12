import cv2
from pyzbar.pyzbar import decode
from gtts import gTTS
import os
import datetime
import time
import re
import pytesseract
import mysql.connector
from mysql.connector import Error


# Connect to the MySQL database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="mydatabase"
)
cursor = conn.cursor()

# Initialize plate cascade
plate_cascade_path = "C:\camnumplate\haskelchick.xml"
plate_cascade = cv2.CascadeClassifier(plate_cascade_path)
# Initialize a set to keep track of scanned number plates
scanned_plates = set()

processed_vehicles = {}

# Capture video and process license plates
cap = cv2.VideoCapture(1)
capture_interval = 60 # Adjust this interval as needed (in seconds)
last_capture_time = time.time() - capture_interval  # Initialize the last capture time

while True:
    success, img = cap.read()

     # Calculate the time elapsed since the last capture
    current_time = time.time()
    time_elapsed = current_time - last_capture_time

    if time_elapsed >= capture_interval:
        # Reset the last capture time
        last_capture_time = current_time

         # Convert the image to grayscale for license plate detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


    maxSize = (999, 999)
    plates = plate_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(999, 999), maxSize=maxSize)
    
    # Detect license plates
    plates = plate_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(100, 30))

    for (x, y, w, h) in plates:
        print(f"Detected plate at (x, y): ({x}, {y}), width: {w}, height: {h}")

        # Extract the license plate region
        plate_region = gray[y:y + h, x:x + w]

     # Draw a green rectangle around the license plate region
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
       # Detected plate at (x, y): (286, 116), width: 142, height: 47

        # Try both single-line and two-line recognition
        plate_text = None  # Initialize plate_text here

        for psm in [6, 7]:  # Using numeric PSM values
           if plate_text is None:
        # Use OCR to extract characters from the license plate
             plate_text = pytesseract.image_to_string(plate_region, config=f'--psm {psm}')
 
        print(f"Extracted Text: {plate_text}")

            # Clean up extracted text (remove whitespace, etc.)
        cleaned_plate_text = ''.join(plate_text.split())



 # Check if the cleaned_plate_text matches a number plate pattern
        plate_pattern = re.compile(r'^[A-Za-z]{2}\d{2}[A-Za-z]{2}\d{4}$')  # Adjust the pattern as needed

        if plate_pattern.match(cleaned_plate_text):
                # Check if the number plate has been scanned before
            if cleaned_plate_text in scanned_plates:
                    # Vehicle is exiting
                print(f"Vehicle {cleaned_plate_text} is exiting.")
                    
                # Store exit date in the database
                exit_date = datetime.datetime.now()
                update_exit_query = "UPDATE log_table SET exit_date = %s WHERE vehicle_number = %s AND exit_date IS NULL"
                cursor.execute(update_exit_query, (exit_date, cleaned_plate_text))
                conn.commit()

                    # Remove the vehicle from the set of scanned plates to allow re-entry
                scanned_plates.remove(cleaned_plate_text)
                time.sleep(30)  # Adjust the delay time as needed

                
            else:
                     # Vehicle is entering
                    # Add the scanned plate to the set
                    scanned_plates.add(cleaned_plate_text)
                    print(f"Vehicle {cleaned_plate_text} is entering.")

    

            # Check if the number plate exists in the users table
            select_query = "SELECT vehicle_type, total_amt FROM users WHERE vehicle_number = %s"
            cursor.execute(select_query, (cleaned_plate_text,))
            result = cursor.fetchone()

            if result:
                vehicle_type = result[0]
                total_amt = result[1]



            # Deduct money and update the users table
                if vehicle_type == 'TwoWheeler':
                  deducted_amt = 4
                elif vehicle_type == 'FourWheeler':
                  deducted_amt = 10

                update_query = "UPDATE users SET total_amt = %s WHERE vehicle_number = %s"
                cursor.execute(update_query, (total_amt - deducted_amt, cleaned_plate_text))
                conn.commit()

                # Insert data into the log_table with the deducted amount
                insert_log_query = "INSERT INTO log_table (vehicle_number, entry_date, vehicle_type, deductions) VALUES (%s, %s, %s, %s)"
                entry_date = datetime.datetime.now()
                

                cursor.execute(insert_log_query, (cleaned_plate_text, entry_date, vehicle_type, deducted_amt))
                conn.commit()




                processed_vehicles[cleaned_plate_text] = current_time
                print(f"Vehicle {cleaned_plate_text} approved. Total amount updated to {total_amt}.")
                
                break
            else:
                print(f"Vehicle {cleaned_plate_text} not found or not approved. Access denied.")
                
                break

    # Create a named window with a GUI normal flag
    cv2.namedWindow("License Plate Detection", cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)

    # Display the processed image in the named window
    cv2.imshow("License Plate Detection", img)


    # Break the loop when 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Close MySQL connection
cursor.close()
conn.close()

# Release the video capture and close OpenCV windows
cap.release()
cv2.destroyAllWindows()






