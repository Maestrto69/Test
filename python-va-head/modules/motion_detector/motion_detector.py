import cv2
import numpy as np

from collections import deque

from drawer.DrawScript import DrawScript

class motion_detector:
	"""docstring for motion_detector"""
	def __init__(self, app):
		self.App = app
		print('[Module][motion_detector]: Init')
		# Default settings
		self.frames_delay = 4

		self.delayed_gray = deque([], self.frames_delay)


	def process(self, frame):
		raw_frame = frame.frame
		module_settings = frame.Cam.getSettings('motion_detector')

		# print("Motion settings : ", module_settings)

		draw_script = DrawScript(module_settings['draw_settings'])

		# Actual Settings
		self.frames_delay = module_settings["frames_delay"]
		self.blur_w = module_settings["blur_w"]
		self.blur_h = module_settings["blur_h"]
		self.detect_level = module_settings["sensitivity"]
		self.dilate_value = module_settings["dilate_value"]
		self.min_area = module_settings["min_area"]

		curr_frame_gray = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2GRAY)
		curr_frame_gray = cv2.GaussianBlur(curr_frame_gray,
										   (self.blur_w, self.blur_h), 0)
		self.delayed_gray.appendleft(curr_frame_gray)

		# Проверки:
		# не получено достаточно кадров для сравнения
		# размеры сравниваемых кадров не совпадают
		# print("MOTION_FRAME_DELAY : ", len(self.delayed_gray))
		# print('MOTION CHECK 1: %s' % len(self.delayed_gray))
		# print('MOTION CHECK 2: %s' % self.frames_delay)
		# print('MOTION CHECK 3: %s' % np.shape(self.delayed_gray[self.frames_delay - 1]))
		# print('MOTION CHECK 4: %s' % np.shape(curr_frame_gray))

		#  or \
		#	np.shape(self.delayed_gray[self.frames_delay - 1]) != np.shape(curr_frame_gray)

		if len(self.delayed_gray) < self.frames_delay:
			# print("Am")
			return draw_script


		diff_frame = cv2.absdiff(self.delayed_gray[self.frames_delay - 1],
								 curr_frame_gray)
		thresh_frame = cv2.threshold(diff_frame, self.detect_level, 255,
									 cv2.THRESH_BINARY)[1]
		thresh_frame = cv2.dilate(thresh_frame, None,
								  iterations=self.dilate_value)

		(all_contours, _) = cv2.findContours(thresh_frame.copy(),
												cv2.RETR_EXTERNAL,
												cv2.CHAIN_APPROX_SIMPLE)
		ret_contours = []
		for contour in all_contours:
			if cv2.contourArea(contour) < self.min_area:
				continue
			(x, y, w, h) = cv2.boundingRect(contour)
			
			#ret_contours.append((x, y, x + w, y + h))
			draw_script.add_box(Box(x, y, x + w, y + h, color=(255, 155, 255)))
			#draw_script.add_box((x, y, x + w, y + h))
      
		# print("MOTION_BOXES : ", draw_script.boxes)

		return draw_script
