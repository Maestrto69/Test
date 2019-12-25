# USAGE
# python encode_faces.py --dataset dataset --encodings encodings.pickle

# import the necessary packages
from imutils import paths
import face_recognition
import dlib
import argparse
import pickle
import cv2
import os
import requests
import numpy
from workWithCams import APIHelper
import time

from modules.face_identification.face_identification_for_add import face_identification

# Добавляет в базу данных один вектор и строку имени
def Go_toDB(encoding, name, imagePath):
    workwithcams = APIHelper('1')
    encoding_ = numpy.array2string(encoding, separator=',')
    json_veсtor = {'vector': encoding_}
    vect_humans = workwithcams.fetchAll('humans') #requests.get("http://localhost:80/api/v1/humans/find.all")
    vect_medias = workwithcams.fetchAll('medias') #requests.get("http://localhost:80/api/v1/medias/find.all")
    en = numpy.array2string(encoding, separator=',')
    image_post = {"name": imagePath}
    media_meta = workwithcams.create('medias', image_post)
    media_id = media_meta["id"]

    if(vect_humans.get("records") is not None):
        human_names = {}

        if vect_humans["count"] > 0:
            for item in vect_humans["records"]:
                if name not in human_names.keys():
                    human_names.update({item["full_name"]: item["_id"]})
        # print("human_names ====", human_names)

        media_cdn_id = media_meta["cdn_id"]
        os.system("curl -F file=%s http://%s/%s" % (imagePath, "localhost:9380", media_cdn_id))
        # print("NAME____=", name)
        if name in human_names.keys():
            # print("___=11111111_____name_________=", name)
            _id_ = human_names[name]
            d_ = {'human_id': _id_, 'media_id': media_id, 'vector': en}
            workwithcams.create('face_models', d_)
            # print("Added %s" % (name))
        else:
            d_ = {'full_name': name, 'gender': 'male', 'dob': "666-06-06"}
            id_page = workwithcams.create('humans', d_)
            _id_ = id_page["id"]
            # print("___=22222222_____id_________=", _id_)
            d_ = {'human_id': _id_, 'media_id': media_id, 'vector': en}
            p = workwithcams.create('face_models', d_)
            # print(p)
            # print("Added Firstly %s" % (name))

    else:
        d_ = {'full_name': name, 'gender': 'male', 'dob': "666-06-06"}
        id_page = workwithcams.create('humans', d_)
        _id_ = id_page["id"]
        # print("___=33333333_____id_________=", _id_)

        d_ = {'human_id': _id_, 'media_id': media_id, 'vector': en}
        p = workwithcams.create('face_models', d_)
        # print (p)
        # print("Added very Firstly %s" % (name))


def all_go_to_DB(dataset, detection_method):
    identificator = face_identification()
    print("[INFO] обработка лиц...")
    imagePaths = list(paths.list_images(dataset))

    # initialize the list of known encodings and known names
    dlib.set_dnn_prefer_smallest_algorithms()

    for (i, name) in enumerate(os.listdir(dataset)):
        print('[INFO] обработка профиля #' + str(i))
        specific_go_to_DB(dataset, name, detection_method, face_identificator=identificator)

def specific_go_to_DB(dataset, name, detection_method='hog', encoding=None, face_identificator=None):
    if encoding is None and face_identificator is None:
        face_identificator = face_identification()

    imagePaths = list(paths.list_images(dataset + os.path.sep + name))
    photos_count = len(imagePaths)
    for i, image_path in enumerate(imagePaths):
        print('[INFO] фото {} из {}'.format(i + 1, photos_count))
        # load the input image and convert it from RGB (OpenCV ordering)
        # to dlib ordering (RGB)
        image = cv2.imread(image_path)
        rgb = image[:, :, ::-1]

        # detect the (x, y)-coordinates of the bounding boxes
        # corresponding to each face in the input image
        boxes = face_recognition.face_locations(rgb, 1, model=detection_method)

        if encoding is None:
            # compute the facial embedding for the face
            face_locations, face_encodings = face_identificator.process(rgb)

            # loop over the encodings
            for encoding in face_encodings:
                # add each encoding + name to our set of known names and
                # encodings
                Go_toDB(encoding, name, image_path)
        else:
            Go_toDB(encoding, name, image_path)


if __name__ == '__main__':
    all_go_to_DB("dataset", "hog")
