import cv2


class Line:
    def __init__(self, point1, point2, color=None, line_thickness=None):
        self.point1 = (point1[0], point1[1])
        self.point2 = (point2[0], point2[1])
        self.color = None if color is None else (color[0], color[1], color[2])
        self.line_thickness = line_thickness


class Box:
    def __init__(self, corner1, corner2, color=None, line_thickness=None):
        self.corner1 = (corner1[0], corner1[1])
        self.corner2 = (corner2[0], corner2[1])
        self.color = None if color is None else (color[0], color[1], color[2])
        self.line_thickness = line_thickness


class Circle:
    def __init__(self, center, radius, color=None, line_thickness=None):
        self.center = (center[0], center[1])
        self.radius = radius
        self.color = None if color is None else (color[0], color[1], color[2])
        self.line_thickness = line_thickness


class Label:
    def __init__(self, text, point, color=None, line_thickness=None,
            font_size=None, font=None, bottom_left_origin=False):
        self.text = text
        self.point = point
        self.color = None if color is None else (color[0], color[1], color[2])
        self.line_thickness = line_thickness
        self.font_size = font_size
        self.font = font
        self.bottom_left_origin = bottom_left_origin


class DrawScript:
    """docstring for DrawScript"""
    default_color = (255, 155, 0)
    default_line_thickness = 1
    default_font_size = 1
    default_font = cv2.FONT_HERSHEY_SIMPLEX

    def __init__(self, draw_settings=None):
        # labels font
        self.color = DrawScript.default_color
        self.line_thickness = DrawScript.default_line_thickness
        self.font_size = DrawScript.default_font_size
        self.font = DrawScript.default_font
        if draw_settings:
            if 'color' in draw_settings:
                c = draw_settings['color']
                self.color = (c[0], c[1], c[2])
            if 'line_thickness' in draw_settings:
                self.line_thickness = draw_settings['line_thickness']
            if 'font_size' in draw_settings:
                self.font_size = draw_settings['font_size']
            if 'font' in draw_settings:
                self.font = draw_settings['font']

        self.lines = []
        self.arrows = []
        self.boxes = []
        self.circles = []
        self.labels = []

    def add_line(self, line):
        self.lines.append(line)

    def add_arrow(self, arrow):
        self.arrows.append(arrow)
        
    def add_box(self, box):
        self.boxes.append(box)

    def add_circle(self, circle):
        self.circles.append(circle)

    def add_label(self, label):
        self.labels.append(label)
