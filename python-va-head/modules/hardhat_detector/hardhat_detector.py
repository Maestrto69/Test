# coding: utf-8

import tensorflow as tf
import numpy as np
import cv2

from modules.object_detector.utils.misc_utils import parse_anchors, read_class_names
from modules.object_detector.utils.nms_utils import gpu_nms
from modules.object_detector.utils.plot_utils import get_color_table, plot_one_box
from modules_helper.deep_sort_tracker_helper.deep_sort_tracker_helper import\
    deep_sort_tracker_helper
from modules_helper.deep_sort_tracker_helper.deep_sort.track import DirectMoveState

from modules.object_detector.model import yolov3

from drawer.DrawScript import *

# import warnings filter
from warnings import simplefilter
# ignore all deprecation warnings
simplefilter(action='ignore', category=DeprecationWarning)


class hardhat_detector:
    """docstring for hardhat_detector"""

    def __init__(self, app):
        self.App = app
        print('[Module][hardhat_detector]: Init')

        self.tracker_lines = {}
        self.tracker_helpers = {}

        self.input_size = [416, 416]
        graph_path = "modules/hardhat_detector/data/hardhat-frcnn-frozen_inference_graph.pb"
        labelspath = "modules/hardhat_detector/data/hardhat_classes.txt"

        self.classes = read_class_names(labelspath)

        config = tf.ConfigProto()
        config.gpu_options.per_process_gpu_memory_fraction = 0.5

        graph = tf.Graph()
        with graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(graph_path, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

        with open(labelspath) as f:
            labels = f.readlines()

        self.classes = [s.strip() for s in labels]

        detection_graph = graph


        self.sess = tf.Session(graph=detection_graph, config=config)

        # Definite input and output Tensors for detection_graph
        self.image_tensor = detection_graph.get_tensor_by_name(
            'image_tensor:0')
        # Each box represents a part of the image where a particular object was detected.
        self.detection_boxes = detection_graph.get_tensor_by_name(
            'detection_boxes:0')
        # Each score represent how level of confidence for each of the objects.
        # Score is shown on the result image, together with the class label.
        self.detection_scores = detection_graph.get_tensor_by_name(
            'detection_scores:0')
        self.detection_classes = detection_graph.get_tensor_by_name(
            'detection_classes:0')
        self.num_detections = detection_graph.get_tensor_by_name(
            'num_detections:0')

    def process(self, frame):
        raw_frame = frame.frame
        module_settings = frame.Cam.getSettings('hardhat_detector')

        draw_script = DrawScript(module_settings['draw_settings'])

        # classes_to_detect
        classes_to_detect = module_settings['target_classes']
        # confidence_level
        confidence_level = module_settings['confidence']

        if len(classes_to_detect) <= 0 or confidence_level > 1:
            return draw_script

        frame_np_expanded = np.expand_dims(raw_frame, axis=0)
        boxes, scores, labels, num = self.sess.run(
            [self.detection_boxes, self.detection_scores, self.detection_classes, self.num_detections],
            feed_dict={self.image_tensor: frame_np_expanded})

        im_height, im_width, _ = raw_frame.shape
        all_boxes = []

        for i in range(boxes.shape[1]):
            all_boxes.append((int(boxes[0, i, 1] * im_width),
                              int(boxes[0, i, 0] * im_height),
                              int(boxes[0, i, 3] * im_width),
                              int(boxes[0, i, 2] * im_height)))

        all_scores = scores[0].tolist()

        all_classes = [int(x) for x in labels[0].tolist()]
        all_labels = [self.classes[int(x) - 1] for x in all_classes]

        ret_boxes = []
        ret_scores = []
        ret_labels = []

        for i in range(len(all_boxes)):
            if all_classes[i] in classes_to_detect and all_scores[i] > confidence_level:
                ret_boxes.append(all_boxes[i])
                ret_scores.append(all_scores[i])
                ret_labels.append(all_labels[i])

                draw_script.add_box(Box((int(all_boxes[i][0]), int(all_boxes[i][1])),
                                        (int(all_boxes[i][2]), int(all_boxes[i][3])),
                                        color=(255, 155, 255)))

                if module_settings['draw_name'] == 1:
                    label = self.classes[int(labels[0][i]) - 1]
                    if module_settings['draw_confid'] == 1:
                        label = " ".join([label, str(round(scores[i] * 100, 2)), '%'])
                    draw_script.add_label(Label(label,
                            (int(all_boxes[i][0]), int(all_boxes[i][1]) + 30),
                            color=(255, 155, 255)))

        return draw_script

    def close(self):
        self.sess.close()
