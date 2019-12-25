# coding: utf-8
import face_recognition
from sklearn import neighbors
import os
import cv2
import time
import pickle
import numpy as np
import modules.face_identification.faceDetector as fd
from modules.face_identification.yolo.yolo import YOLO
from PIL import Image
import tensorflow as tf



class face_identification:
    """docstring for face_identification"""

    def __init__(self):
        self.faceDetector = YOLO()

    def process(self, frame):
        converted = np.zeros(np.shape(frame), np.uint8)
        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, dst=converted)
        image = Image.fromarray(converted)
        face_locations = self.faceDetector.detect_image(image)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        return face_locations, face_encodings

    def close(self):
        self.sess.close()
