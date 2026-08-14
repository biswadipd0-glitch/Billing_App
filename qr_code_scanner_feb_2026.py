import cv2
from pyzbar.pyzbar import decode

from warnings import filterwarnings
filterwarnings(action='ignore')
def qr_code_scanner():
    cap = cv2.VideoCapture(1)
    while True:

        ret, frame = cap.read()

        try:
            decoded_objs = decode(frame)
        except Exception as e:
            print("Error decoding QR code:", e)
            continue
        cv2.imshow('QR Code Scanner', frame)

        if decoded_objs:
            for obj in decoded_objs:
                #print(obj.data.decode())
                scanned_text=obj.data.decode()
                p_id=scanned_text.split('-')[0]
                #print(p_id)
                #return obj.data.decode()
                return p_id

            break  # Break out of the loop once a QR code is detected

        # Wait for the 'q' key to be pressed to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the camera and close all windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    qr_code_scanner()
