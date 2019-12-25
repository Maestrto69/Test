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


class object_detector:
    """docstring for object_detector"""

    def __init__(self, app):
        self.App = app
        print('[Module][object_detector]: Init')

        self.tracker_lines = {}
        self.tracker_helpers = {}

        self.input_size = [416, 416]
        model_path = "modules/object_detector/data/darknet_weights/yolov3.ckpt"
        anchors_path = "modules/object_detector/data/yolo_anchors.txt"
        labels_path = "modules/object_detector/data/coco.names"

        anchors = parse_anchors(anchors_path)
        self.classes = read_class_names(labels_path)
        num_class = len(self.classes)

        config = tf.ConfigProto()
        config.gpu_options.per_process_gpu_memory_fraction = 0.5

        self.sess = tf.Session(config=config)
        self.input_data = tf.placeholder(tf.float32, [1, self.input_size[1], self.input_size[0], 3], name='input_data')
        yolo_model = yolov3(num_class, anchors)

        with tf.variable_scope('yolov3'):
            pred_feature_maps = yolo_model.forward(self.input_data, False)
        pred_boxes, pred_confs, pred_probs = yolo_model.predict(pred_feature_maps)

        pred_scores = pred_confs * pred_probs

        self.boxes, self.scores, self.labels = gpu_nms(pred_boxes, pred_scores, num_class, max_boxes=100,
                                                       score_thresh=0.7, iou_thresh=0.5)

        self.saver = tf.train.Saver()
        self.saver.restore(self.sess, model_path)

    def process(self, frame):
        raw_frame = frame.frame
        module_settings = frame.Cam.getSettings('object_detector')

        draw_script = DrawScript(module_settings['draw_settings'])

        # classes_to_detect
        classes_to_detect = module_settings['target_classes']
        # confidence_level
        confidence_level = module_settings['confidence']

        if len(classes_to_detect) <= 0 or confidence_level > 1:
            return draw_script

        height, width = raw_frame.shape[:2]
        resized = np.zeros((416, 416, 3), np.uint8)
        cv2.resize(raw_frame, (416, 416), dst=resized, interpolation=cv2.INTER_LINEAR)
        converted = np.zeros((416, 416, 3), np.uint8)
        cv2.cvtColor(resized, cv2.COLOR_BGR2RGB, dst=converted)
        converted_as_float = np.asarray(converted, np.float32)
        converted_as_float[np.newaxis, :] /= 255.
        boxes_, scores_, labels_ = self.sess.run([self.boxes, self.scores, self.labels],
                                                 feed_dict={self.input_data: [converted_as_float]})

        # rescale the coordinates to the original image
        boxes_[:, 0] *= (width / float(self.input_size[0]))
        boxes_[:, 2] *= (width / float(self.input_size[0]))
        boxes_[:, 1] *= (height / float(self.input_size[1]))
        boxes_[:, 3] *= (height / float(self.input_size[1]))
        for i in range(len(boxes_)):
            if labels_[i] in classes_to_detect and scores_[i] > 0.1:  # TODO: почему всегда 0.1?
                draw_script.add_box(Box((int(boxes_[i][0]), int(boxes_[i][1])),
                        (int(boxes_[i][2]), int(boxes_[i][3]))))

                if module_settings['draw_name'] == 1:
                    label = self.classes[labels_[i]]
                    if module_settings['draw_confid'] == 1:
                        label = " ".join([label, str(round(scores_[i] * 100, 2)), '%'])
                    draw_script.add_label(Label(label, 
                            (int(boxes_[i][0]) + 10, int(boxes_[i][1]) + 35)))

                center = np.array([int((boxes_[i][0] + boxes_[i][2]) / 2),
                        int((boxes_[i][1] + boxes_[i][3]) / 2)])

        tracker_mode = module_settings['tracker_mode']
        if tracker_mode > 0:
            # Переводим нормализованные координаты в полезные, лул
            if 'regions' in module_settings:
                for i in range(len(module_settings['regions'])):
                    for j in range(len(module_settings['regions'][i]['points'])):
                        if isinstance(module_settings['regions'][i]['points'][j][0], float):
                            module_settings['regions'][i]['points'][j][0] = int(module_settings['regions'][i]['points'][j][0] * frame.frame.shape[1])
                            module_settings['regions'][i]['points'][j][1] = int(module_settings['regions'][i]['points'][j][1] * frame.frame.shape[0])
            if 'direction_regions' in module_settings:
                for i in range(len(module_settings['direction_regions'])):
                    for j in range(len(module_settings['direction_regions'][i]['points'])):
                        if isinstance(module_settings['direction_regions'][i]['points'][j][0], float):
                            module_settings['direction_regions'][i]['points'][j][0] = int(module_settings['direction_regions'][i]['points'][j][0] * frame.frame.shape[1])
                            module_settings['direction_regions'][i]['points'][j][1] = int(module_settings['direction_regions'][i]['points'][j][1] * frame.frame.shape[0])
                    for j in range(len(module_settings['direction_regions'][i]['direction'])):
                        if isinstance(module_settings['direction_regions'][i]['direction'][j][0], float):
                            module_settings['direction_regions'][i]['direction'][j][0] = int(module_settings['direction_regions'][i]['direction'][j][0] * frame.frame.shape[1])
                            module_settings['direction_regions'][i]['direction'][j][1] = int(module_settings['direction_regions'][i]['direction'][j][1] * frame.frame.shape[0])
            if 'lines' in module_settings:
                for i in range(len(module_settings['lines'])):
                    for j in range(len(module_settings['lines'][i]['points'])):
                        if isinstance(module_settings['lines'][i]['points'][j][0], float):
                            module_settings['lines'][i]['points'][j][0] = int(module_settings['lines'][i]['points'][j][0] * frame.frame.shape[1])
                            module_settings['lines'][i]['points'][j][1] = int(module_settings['lines'][i]['points'][j][1] * frame.frame.shape[0])

            t_boxes = []
            t_labels = []
            t_scores = []

            for i in range(len(boxes_)):
                if labels_[i] in classes_to_detect and scores_[i] > 0.1:
                    t_boxes.append(boxes_[i])
                    t_labels.append(labels_[i])
                    t_scores.append(scores_[i])

            draw_script.boxes = []
            draw_script.labels = []

            cam_id = frame.Cam.getId()

            if not cam_id in self.tracker_helpers:
                self.tracker_helpers[cam_id] = deep_sort_tracker_helper()

            t_boxes = [[box[0], box[1], box[2] - box[0], box[3] - box[1]] for\
                    box in t_boxes]
            tracker_boxes, tracker_labels, tracker_circles, tracker_lines =\
                    self.tracker_helpers[cam_id].track(t_boxes, t_scores,\
                    t_labels, module_settings, frame, self.App)
            
            for line in module_settings['lines']:
                if line['is_active'] == 1:
                    draw_script.add_line(Line(*line['points'], color=line['color']))
            for region in module_settings['regions']:
                if region['is_active'] == 1:
                    points = region['points']
                    for i in range(len(points) - 1):
                        draw_script.add_line(Line(points[i], points[i + 1],
                                color=region['color']))
                    draw_script.add_line(Line(points[-1], points[0],
                            color=region['color']))
            for region in module_settings['direction_regions']:
                if region['is_active'] == 1:
                    points = region['points']
                    x = np.mean([p[0] for p in points])
                    y = np.mean([p[1] for p in points])
                    center = [int(x), int(y)]
                    startDirVector, endDirVector = region['direction']
                    draw_script.add_arrow(Line(startDirVector, endDirVector,
                            color=region['color']))

                    for i in range(len(points) - 1):
                        draw_script.add_line(Line(points[i], points[i + 1],
                                color=region['color']))
                    draw_script.add_line(Line(points[-1], points[0],
                            color=region['color']))

            for line in tracker_lines:
                draw_script.add_line(line)
            for box in tracker_boxes:
                draw_script.add_box(box)
            for label in tracker_labels:
                draw_script.add_label(label)
            for circle in tracker_circles:
                draw_script.add_circle(circle)
        return draw_script

    def close(self):
        self.sess.close()
