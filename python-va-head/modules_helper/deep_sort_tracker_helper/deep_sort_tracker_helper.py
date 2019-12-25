#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import

import numpy as np
import math

from drawer.DrawScript import *
from modules_helper.deep_sort_tracker_helper.deep_sort.track import\
    DirectMoveState
from .deep_sort import preprocessing
from .deep_sort import nn_matching
from .deep_sort.detection import Detection
from .deep_sort.tracker import Tracker
from .tools import generate_detections as gdet
from app.Event import Event, EventLevel


# P, A, B - точки [x, y]
# P - отдельная точка
# A, B - точки, принадлежащие линии, A != B
def get_point_pos_to_line(P, A, B):
    return (P[0] - A[0]) * (B[1] - A[1]) - (P[1] - A[1]) * (B[0] - A[0])

# segment1, segment2 - отрезки [[x0, y0], [x1, y1]]
def are_segments_intersected(segment1, segment2):
    p1, p2 = segment1
    q1, q2 = segment2
    A = [[p2[0]-p1[0], q1[0]-q2[0]], [p2[1]-p1[1], q1[1]-q2[1]]]
    b = [[q1[0]-p1[0]], [q1[1]-p1[1]]]
    x = None
    try:
        x = np.linalg.solve(A, b)
    except np.linalg.LinAlgError as err:
        return False
    return 0 <= x[0][0] <= 1 and 0 <= x[1][0] <= 1

# point - точка [x, y]
# polygon - многоугольник [[x0, y0], [x1, y1], [x2, y2], ...]
def is_point_in_polygon(point, polygon):
    x0, y0 = point

    result = False
    i = 0
    j = len(polygon) - 1
    while i < len(polygon):
        x1, y1 = polygon[i]
        x2, y2 = polygon[j]
        # orig: if ((((yp[i]<=y) && (y<yp[j])) || ((yp[j]<=y) && (y<yp[i]))) && (yp[j]-yp[i]!=0&&x > (xp[j] - xp[i]) * (y - yp[i]) / (yp[j] - yp[i]) + xp[i]))
        # edi1: if ( ((y1<=y0) && (y0<y2) || (y2<=y0) && (y0<y1)) && (y2-y1!=0&&x0 > (x0 - x1) * (y0 - y1) / (y2 - y1) + x1) ):
        """if ((y1 <= y0 < y2 or y2 <= y0 < y1) and\
                (y2 - y1 != 0 and x0 > (x0 - x1) * (y0 - y1) / (y2 - y1) + x1)):"""
        if ((y1 <= y0 < y2 or y2 <= y0 < y1) and\
                (y2 - y1 != 0 and x0 > (x2 - x1) * (y0 - y1) / (y2 - y1) + x1)):
            result = not result
        j = i
        i += 1
    return result

# a, b - векторы [x, y, ...]
def calc_angle(a, b):
    scalar_prod = 0
    a_length = 0
    b_length = 0
    for i in range(len(a)):
        scalar_prod += a[i] * b[i]
        a_length += a[i] * a[i]
        b_length += b[i] * b[i]
    a_length = math.sqrt(a_length)
    b_length = math.sqrt(b_length)
    denominator = a_length * b_length
    return math.acos(scalar_prod / denominator) if denominator != 0 else 0


"""class TrackerMode:
    Disabled = 0
    ForbiddenRegion = 1
    CurrentCountRegion = 2
    NoVehicleRegion = 3
    ControlRegion = 4
    DirectMoveRegion = 5
    CounterLine = 6"""
class RegionType:
    ForbiddenRegion = 'forbidden_zone'
    CurrentCountRegion = 'current_count_zone'
    NoVehicleRegion = 'no_vehicle_zone'
    ControlRegion = 'control_zone'
class DirectionRegionType:
    DirectMoveRegion = 'direct_move_zone'
class LineType:
    CounterLine = 'tracker_line'


class deep_sort_tracker_helper:
    def __init__(self):
        # Параметры
        self.max_cosine_distance = 0.3  # косинусный коэффициент для определения схожести объекта на разных кадрах
        self.nn_budget = 1000  # из справки: If not None, fix samples per class to at most this number. Removes the oldest samples when the budget is reached.
        self.nms_max_overlap = 1.0  # параметр для NMS
        self.track_ttl = 1000  # время жизни информации об объекте в списке обнаруженных после его потери из кадра (в кадрах)
        # deep_sort
        model_filename = 'modules_helper/deep_sort_tracker_helper/model_data/mars-small128.pb'
        self.encoder = gdet.create_box_encoder(model_filename, batch_size=1)

        self.metric = nn_matching.NearestNeighborDistanceMetric('cosine', self.max_cosine_distance, self.nn_budget)
        # video_capture = cv2.VideoCapture(0)
        self.tracker = Tracker(self.metric, self.track_ttl)

        self.counter_regions = {}
        self.counter_lines = {}

        self.crossed_a_to_b = 0
        self.crossed_b_to_a = 0

    def track(self, boxes, scores, classes, module_settings, frame, app=None):
        ret_boxes = []
        ret_labels = []
        ret_circles = []
        ret_lines = []

        features = self.encoder(frame.frame, boxes)
        detections = [Detection(bbox, score, feature, class_) for\
                bbox, score, feature, class_ in\
                zip(boxes, scores, features, classes)]

        # Run non-maxima suppression.
        boxes = np.array([d.tlwh for d in detections])
        scores = np.array([d.confidence for d in detections])
        indices = preprocessing.non_max_suppression(boxes, self.nms_max_overlap, scores)
        detections = [detections[i] for i in indices]

        # Call the tracker
        self.tracker.predict()
        self.tracker.update(detections)

        self.check_for_events(module_settings, frame)
        for track in self.tracker.tracks:
            track.is_checked = True

        for track in self.tracker.tracks:
            # TODO: хотим ли рисовать след, если объект временно пропал с кадра?
            if not track.should_be_drawn():
                continue

            color = None
            if track.direct_move_state == DirectMoveState.Yellow:
                color = (0, 240, 255)
            # if track.has_crossed_line or track.is_in_forbidden_region or\
            if track.is_in_forbidden_region or\
                    track.direct_move_state == DirectMoveState.Red:
                color = (0, 0, 200)

            prev_point = None
            for point in track.history:
                ret_circles.append(Circle(point, 5, color=color))
                if prev_point is not None:
                    ret_lines.append(Line(point, prev_point, color=color))
                prev_point = point
            last_pos = track.get_last_position()
            if last_pos is not None and len(track.history) > 0:
                ret_lines.append(Line(last_pos, track.history[0], color=color))
                ret_circles.append(Circle(last_pos, 5, color=color))

            bbox = track.to_tlbr()
            ret_boxes.append(Box((int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), color=color))
            # ret_labels.append(Label(str(track.track_id), (int(bbox[0]), int(bbox[1]) + 80), color=(200, 40, 40), line_thickness=3, font_size=3))
        return ret_boxes, ret_labels, ret_circles, ret_lines

    def check_for_events(self, module_settings, frame):
        current_counts = {}
        for track in self.tracker.tracks:
            # if len(track.history) < 1:
            # if track.is_checked or len(track.history) < 1:
            is_in_region = False
            for region in module_settings['regions']:
                if region['is_active'] == 1:
                    region_id = region['_id']
                    region_type = region['type']
                    if (region_type == RegionType.CurrentCountRegion or
                            region_type == RegionType.ControlRegion) and\
                            region_id not in current_counts:
                        current_counts[region_id] = 0
                    last_pos = track.get_last_position()
                    if last_pos is not None and is_point_in_polygon(
                            last_pos, region['points']):
                        """if (region_type == RegionType.ForbiddenRegion or
                                region_type == RegionType.NoVehicleRegion) and\
                                not track.is_checked:"""
                        if region_type == RegionType.ForbiddenRegion or\
                                region_type == RegionType.NoVehicleRegion:
                            is_in_region = True
                        elif region_type == RegionType.CurrentCountRegion or\
                                region_type == RegionType.ControlRegion:
                            current_counts[region_id] += 1
            if is_in_region != track.is_in_forbidden_region:
                print('[Module][tracker] Объект №{} {} запретную зону'.\
                        format(track.track_id,
                        'вошёл в' if is_in_region else 'покинул'))
                if is_in_region:
                    Event.create_event(frame.frame, EventLevel.Warn,
                            frame.Cam.get('title') + ": детектор объектов",
                            'В запрещённой зоне зафиксирован объект',
                            frame.Cam.getId())
                track.is_in_forbidden_region = is_in_region
            
            if track.is_checked or len(track.history) < 2:
                continue
            is_in_region = False
            direct_move_state = DirectMoveState.Green
            for region in module_settings['direction_regions']:
                if region['is_active'] == 1:
                    if is_point_in_polygon(track.history[0], region['points']):
                        is_in_region = True
                        a_beg, a_end = region['direction']
                        a = [a_end[0] - a_beg[0], a_end[1] - a_beg[1]]
                        b_beg, b_end = track.history[1], track.history[0]
                        b = [b_end[0] - b_beg[0], b_end[1] - b_beg[1]]
                        angle = np.rad2deg(calc_angle(a, b))

                        # TODO: добавить параметры зелёного, жёлтого и красного углов
                        # от 0 до 40 - зелёный
                        # от 40 до 90 - жёлтый
                        # от 90 до 180 - красный
                        deg_green = 40
                        deg_yellow = 90
                        # красный угол - остальное
                        if deg_green < angle <= deg_yellow and direct_move_state < DirectMoveState.Red:
                            direct_move_state = DirectMoveState.Yellow
                            print('[Module][tracker] Объект №{} двигается по смещённой трактории (YELLOW)'.\
                                    format(track.track_id))
                        elif angle > deg_yellow:
                            direct_move_state = DirectMoveState.Red
                            print('[Module][tracker] Объект №{} двигается против разрешённого направления (RED)'.\
                                    format(track.track_id))
                            if track.direct_move_state != DirectMoveState.Red:
                                Event.create_event(frame.frame, EventLevel.Warn,
                                        frame.Cam.get('title') + ": детектор объектов",
                                        'Зафиксировано движение в запрещённом направлении',
                                        frame.Cam.getId())
            track.direct_move_state = direct_move_state

            p0 = track.history[0]  # последняя точка отслеживаемого объекта
            p1 = track.history[1]  # предпоследняя точка отслеживаемого объекта
            last_track_segment = [[p1[0], p1[1]], [p0[0], p0[1]]]
            for line in module_settings['lines']:
                if line['is_active'] == 1:
                    line_id = line['_id']
                    if line_id not in self.counter_lines:
                        self.counter_lines[line_id] = [0, 0]  # пересечения A->B и B->A
                    if are_segments_intersected(line['points'], last_track_segment):
                        track.has_crossed_line = True
                        before = self.counter_lines[line_id]
                        if get_point_pos_to_line(p0, *line['points']) < 0:
                            self.counter_lines[line_id] = [before[0] + 1, before[1]]
                            Event.create_event(frame.frame, EventLevel.Log,
                                    frame.Cam.get('title') + ": детектор объектов",
                                    'Зафиксировано объектов в направлении A->B: {}'.
                                    format(self.counter_lines[line_id][0]),
                                    frame.Cam.getId())
                        else:
                            self.counter_lines[line_id] = [before[0], before[1] + 1]
                            Event.create_event(frame.frame, EventLevel.Log,
                                    frame.Cam.get('title') + ": детектор объектов",
                                    'Зафиксировано объектов в направлении B->A: {}'.
                                    format(self.counter_lines[line_id][1]),
                                    frame.Cam.getId())
                        print('[Module][tracker] [{:05d}:{:05d}] Объект №{} пересёк линию'. \
                              format(self.crossed_a_to_b, self.crossed_b_to_a,
                                     track.track_id))
                        break

        # Проверим изменения количества объектов в регионах с подсчётом
        for region in module_settings['regions']:
            if region['is_active'] == 1:
                region_id = region['_id']
                region_type = region['type']
                if region_type == RegionType.CurrentCountRegion or\
                        region_type == RegionType.ControlRegion:
                    is_counter_changed = False
                    if region_id in self.counter_regions:
                        if region_id in current_counts:
                            if self.counter_regions[region_id] != current_counts[region_id]:
                                self.counter_regions[region_id] = current_counts[region_id]
                                is_counter_changed = True
                        else:
                            pass
                            self.counter_regions[region_id] = 0
                            is_counter_changed = True
                    else:
                        if region_id in current_counts:
                            self.counter_regions[region_id] = current_counts[region_id]
                            is_counter_changed = True

                    if is_counter_changed:
                        if region_type == RegionType.CurrentCountRegion:
                            Event.create_event(frame.frame, EventLevel.Log,
                                    frame.Cam.get('title') + ": детектор объектов",
                                    'Число объектов в регионе "{}" стало равно {}'.
                                    format(region['title'], self.counter_regions[region_id]),
                                    frame.Cam.getId())
                        elif region_type == RegionType.ControlRegion and\
                                self.counter_regions[region_id] == 0:
                            Event.create_event(frame.frame, EventLevel.Warn,
                                    frame.Cam.get('title') + ": детектор объектов",
                                    'Сотрудник покинул свой пост', frame.Cam.getId())
