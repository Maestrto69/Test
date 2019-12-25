import os
import cv2
import numpy as np

from modules.face_identification.face_identification_for_add import face_identification

from aza_All_Go_to_DB import all_go_to_DB, specific_go_to_DB


def open_faces_cap():
    cap = cv2.VideoCapture(0)
    font = cv2.FONT_HERSHEY_SIMPLEX
    isRec = False
    i = 0
    identificator = face_identification()

    photos = []
    bool_running = True
    while(bool_running):
        _, frame = cap.read()
        dim = frame.shape
        rx0 = int(dim[1]/2) - 150
        rx1 = int(dim[1]/2) + 150
        ry0 = int(dim[0]/2) - 200
        ry1 = int(dim[0]/2) + 200
        rectframe = frame[ry0:ry1, rx0:rx1]
        rgb = np.zeros(dim, np.uint8)
        cv2.cvtColor(rectframe, cv2.COLOR_BGR2RGB, dst=rgb)
    
        # face_locations = face_recognition.face_locations(rgb, 1, "hog")
        face_locations, face_encodings = identificator.process(rectframe)
        cv2.imshow('rect', rectframe)

        # for (top, right, bottom, left) in face_locations:
        if len(face_locations) < 1:
            print('No faces found')
        elif len(face_locations) > 1:
            print('More than 1 face found')
            for (y0, x1, y1, x0) in face_locations:
                cv2.rectangle(frame, (rx0+x0, ry0+y0), (rx0+x1, ry0+y1), (0, 0, 230), 2)
                print(y0, x1, y1, x0)
        else:
            y0, x1, y1, x0 = face_locations[0]
            cv2.rectangle(frame, (rx0+x0, ry0+y0), (rx0+x1, ry0+y1), (0, 230, 0), 2)

            if(isRec):
                print("Taking image %d:" % i)
                y0, x1, y1, x0 = face_locations[0]
                photos.append(rectframe[y0:y1, x0:x1])
                i += 1
                print("  image done." if _ else "  Error while taking image...")
                if(i >= 1):
                    isRec = False
                    j = 0
                    name = input('Введите имя человека: ')
                    if len(name) > 0:
                        for photo in photos:
                            if not os.path.exists("dataset/%s" % name):
                                os.makedirs("dataset/%s" % name)

                            cv2.imwrite("dataset/%s/%s%d.jpg" % (name, name, j), photo)
                            j += 1
                    photos.clear()

                    #os.system("python3.5 encode_faces.py -i dataset")
                    if len(face_encodings) > 0:
                        specific_go_to_DB("dataset", name, "hog", encoding=face_encodings[0])

                    cap.release()
                    cv2.destroyWindow("Autentification")
                    bool_running = False

        cv2.rectangle(frame, (int(dim[1] / 2) - 150, int(dim[0] / 2) - 200), (int(dim[1] / 2) + 150, int(dim[0] / 2) + 200),
                      (100, 100, 100) if isRec else (225, 225, 0), 4)
        cv2.putText(frame, 'Put your face into rectangle', (5, 470), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.imshow("Autentification", frame)
        if cv2.waitKey(1) & 0xFF == ord('r'):
            isRec = True
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyWindow("Autentification")

if __name__ == '__main__':
    open_faces_cap()