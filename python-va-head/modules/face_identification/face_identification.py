# coding: utf-8
import face_recognition
import requests
from sklearn import neighbors
import os
import cv2
import time
import pickle
import numpy as np
from PIL import Image
from app.Event import *
import modules.face_identification.faceDetector as fd
from drawer.DrawScript import *
from keras.models import load_model
import keras
import pandas as pd
from tensorflow import Graph, Session
import tensorflow as tf
import modules_helper.face_identification_dlc as dlc
import copy

class face_identification:
    """docstring for face_identification"""

    def __init__(self, app):
        self.App = app
        print('[Module][face_identification]: Init')
        
        self.confidence = 0.65

        ## Emotions and other face additional stuff for face id
        self.COLS = ['Male', 'Asian', 'White', 'Black','Indian','0-5','10-15','20-35','45-65','65+','No Eyewear']
        self.COLS = ['Male', 'Asian', 'White', 'Black','Indian','Baby','Teenager','Young','Middle age','Elder','No Eyewear']
        emotion_model_path = 'modules/face_identification/fer2013_mini_XCEPTION.46-0.82.hdf5'
        self.emotion_labels = {0: 'angry', 1: 'happy', 2: 'surprise', 3: 'neutral'}

        self.graph = tf.get_default_graph()
        self.emotion_classifier = load_model(emotion_model_path, compile=False)
        self.emotion_target_size = self.emotion_classifier.input_shape[1:3]
        print(self.emotion_target_size)
        self.emotion_offsets = (20, 40)

        with open('modules/face_identification/face_model.pkl', 'rb') as f:
            self.clf, self.labels = pickle.load(f, encoding='latin1')

        # Init a class for face detection
        self.faceDetector = fd.TensorflowFaceDetector()
        self.DetectedName = []
        self.timeFirst = 0

    def process(self, frame):
        raw_frame = frame.frame
        module_settings = frame.Cam.getSettings('face_identification')

        draw_script = DrawScript(module_settings['draw_settings'])

        if self.confidence > 1:
            return draw_script

        #gray = np.zeros((raw_frame.shape[0], raw_frame.shape[1], 1), np.uint8)
        #cv2.cvtColor(raw_frame, cv2.COLOR_BGR2GRAY, dst=gray)

        gray = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2GRAY)

        rgb = np.zeros(np.shape(raw_frame), np.uint8)
        cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB, dst=rgb)

        # Find all the faces in the test image using SSD networks(Tensorflow)
        face_locations = self.faceDetector.run(rgb)

        # Predict all the faces in the test image using the trained classifier
        image_faces_encodings = face_recognition.face_encodings(rgb, face_locations)

        if image_faces_encodings != []:
            pred = pd.DataFrame(self.clf.predict_proba(image_faces_encodings),
                                columns = self.labels)
            # prediction = pred.loc[:, self.COLS]
        for i in range(len(face_locations)):

            try:
               prediction_face = ''
               prediction_face = dlc.get_prediction_dataframe(prediction, i)
            except:
               prediction_face = ''

            resized = np.zeros((64, 64), np.uint8)
            cv2.resize(gray[face_locations[i][0]:face_locations[i][2], face_locations[i][3]:face_locations[i][1]],(64,64), dst=resized)
            # gray_face = cv2.resize(gray[face_locations[i][0]:face_locations[i][2], face_locations[i][3]:face_locations[i][1]],(64,64))
            gray_face = dlc.preprocess_input(resized, False)
            gray_face = np.expand_dims(gray_face, 0)
            gray_face = np.expand_dims(gray_face, -1)
            with self.graph.as_default():
            emotion_label_arg = np.argmax(self.emotion_classifier.predict(gray_face))
            emotion_text = self.emotion_labels[emotion_label_arg]
            draw_script.add_label(Label(prediction_face + ' ' + emotion_text, (int(face_locations[i][3]), int(face_locations[i][0]) - 20), color=(0, 255, 0), line_thickness=3, font_size=1.5))
            # Prediction by KNN with kdtree
            name = 'Unknown'
            confidence = 0
            try:
                encoding_ = np.array2string(image_faces_encodings[i], separator=',')

                face_vector = {'vector': encoding_}
                dat = self.App.Api.findFaceByVector(face_vector)

                # FACEREC_CONF
                confidence = max(0, 1 - dat["distance"]*0.8)
                if (confidence >= self.confidence):
                    human = dat['human']
                    name = human['full_name']
                    human_id = human['_id']
            except Exception as e:
                print(e)

            if confidence > self.confidence:
                draw_script.add_label(Label(name,
                        (face_locations[i][3] + 10, face_locations[i][0] + 35),
                        color=(0, 255, 0)))
                draw_script.add_box(Box(
                        (face_locations[i][1], face_locations[i][2]),
                        (face_locations[i][3], face_locations[i][0]),
                        color=[0,255,0]))
              
                if name not in self.DetectedName and name != 'Unknown':
                    Event.create_event(frame.frame, EventLevel.Log,
                            frame.Cam.get('title') + ' : Идентифицировна персона',
                            'Обнаружен ' + name,
                            frame.Cam.getId())
                    self.DetectedName.append(name)
                    self.timeFirst = time.time()
                if time.time() - self.timeFirst > 10:
                    self.DetectedName.clear()
            else:
                # draw_script.add_label(Label('Unknown', (int(face_locations[i][3]), int(face_locations[i][0]) - 20), color=(0, 0, 255), line_thickness=3, font_size=1.5))
                draw_script.add_box(Box((int(face_locations[i][1]), int(face_locations[i][2])), (int(face_locations[i][3]), int(face_locations[i][0])), color=(0, 0, 255), line_thickness=3))
        return draw_script

    def add_facemodel(self, human_id, media_id, image):
        rgb = np.zeros(np.shape(image), np.uint8)
        cv2.cvtColor(image, cv2.COLOR_BGR2RGB, dst=rgb)

        # Find all the faces in the test image using SSD networks(Tensorflow)
        face_locations = self.faceDetector.run(rgb)

        # Predict all the faces in the test image using the trained classifier
        image_faces_encodings = face_recognition.face_encodings(rgb, face_locations)

        if len(face_locations) > 0:
            try:
                encoding_ = np.array2string(image_faces_encodings[0], separator=',')
                body = { 'human_id': human_id, 'media_id': media_id, 'vector': encoding_ }
                res = self.App.Api.create('face_models', body)
            except Exception as e:
                print(e)

    def close(self):
        self.sess.close()
