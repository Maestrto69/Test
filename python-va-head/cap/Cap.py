import cv2
import pafy

from threading import Thread

from cap.Frame import Frame

class Cap:
	"""docstring for Cap"""
	def __init__(self, app, cam):
		self.App = app
		self.Cam = cam
		self.Cap = None

		self.is_run = True

		self.frame_process = False
		# self.frame_th = None

		self.Thread = Thread(target=self.run)
		self.Thread.start()

	def get_link(self):
		link = self.Cam.get('link')

		if (link.find('youtube') == -1):
			return link
		else:
			youtube_stream = pafy.new(link)
			return youtube_stream.getbest(preftype='mp4').url

	def run(self):
		print('[Cap][%s]: Start thread' % self.Cam.getId())

		self.Cap = cv2.VideoCapture(self.get_link())

		while(True):
			if self.Cap.isOpened():
				if not self.is_run:
					break

				if self.frame_process:
					_ = self.Cap.grab()
					continue

				grabbed, frame = self.Cap.read()
				if grabbed == True:
					self.frame_process = True
					# self.frame_th = Thread(target=self.App.FrameHandler.process, args=[Frame(frame, self.Cam)])
					# self.frame_th.start()
					Thread(target=self.App.FrameHandler.process, args=[Frame(frame, self.Cam)]).start()
			else:
				self.Cap = cv2.VideoCapture(self.get_link())
				print('[Cap][%s]: Reconnected' % self.Cam.getId())
