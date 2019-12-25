import time

class Frame:
	"""docstring for Frame"""
	def __init__(self, frame, cam):
		self.time = time.time()
		self.frame = frame
		self.Cam = cam
