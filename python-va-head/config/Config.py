
class Config:
	"""docstring for Config"""
	def __init__(self):
		self.api_endpoint = 'http://172.16.238.10:80/api'
		self.facedetection_endpoint = 'http://172.16.238.10:80/facedetection'
		#self.facedetection_endpoint = 'http://127.0.0.1:80/facedetection'
		self.api_version = 'v1'
		#self.sockets_endpoint = 'http://127.0.0.1:3000'
		self.sockets_endpoint = 'http://172.16.238.15:3000'
		self.sockets_reconnect_sleep = 3 # on startup if connection refused (sec)
		self.no_cams_retry_sleep = 3 # on startup if no cams (sec)
		self.dvr_duration = 60
