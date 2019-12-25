import cv2
import json

class Drawer:
    """docstring for Drawer"""
    def __init__(self, app):
        self.App = app

    def process(self, frame, draw_scripts):
        for draw_script in draw_scripts:
            for line in draw_script.lines:
                cv2.line(frame, line.point1, line.point2,
                        line.color or draw_script.color,
                        line.line_thickness or draw_script.line_thickness)
            for arrow in draw_script.arrows:
                cv2.arrowedLine(frame, arrow.point1, arrow.point2,
                        arrow.color or draw_script.color,
                        arrow.line_thickness or draw_script.line_thickness)
            for box in draw_script.boxes:
                cv2.rectangle(frame, box.corner1, box.corner2,
                        box.color or draw_script.color,
                        box.line_thickness or draw_script.line_thickness)
            for circle in draw_script.circles:
                cv2.circle(frame, circle.center, circle.radius,
                        circle.color or draw_script.color,
                        circle.line_thickness or draw_script.line_thickness)
            for label in draw_script.labels:
                cv2.putText(frame, label.text, label.point,
                        label.font or draw_script.font,
                        label.font_size or draw_script.font_size,
                        label.color or draw_script.color,
                        label.line_thickness or draw_script.line_thickness,
                        label.bottom_left_origin)
        return frame
