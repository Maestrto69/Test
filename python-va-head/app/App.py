import os
import sys
import time

from api.Api import Api
from sockets.Sockets import Sockets

from api.models.Cam import Cam
from cap.Cap import Cap

from app.FrameHandler import FrameHandler
from drawer.Drawer import Drawer
from app.Event import Event

class App:
	"""docstring for App"""
	def __init__(self, config):
		self.Config = config

		self.Api = Api(self)
		self.Sockets = Sockets(self)
		self.FrameHandler = FrameHandler(self)
		self.Drawer = Drawer(self)
		self.Event = Event(self)

		self.Cams = {}
		self.Modules = {}

		self.Caps = {}

		self.init_cams()
		self.init_modules()
		self.init_caps()

	def init_cams(self):
		cams = self.Api.findAll('cams')

		if cams:
			for cam in cams:
				self.Cams[cam['_id']] = Cam(cam['_id'])
				self.Cams[cam['_id']].load(cam)
		else:
			print('[App]: No cams, retry.. (theard blocked)')
			time.sleep(self.Config.no_cams_retry_sleep)
			self.init_cams()

		print('[App]: Cams loaded')

	def init_modules(self):
		for module in next(os.walk("/".join([ os.path.abspath(os.path.dirname(sys.argv[0])), 'modules' ])))[1]:
			module_class = getattr(__import__(".".join([ 'modules', module, module ]), fromlist=[module]), module)
			self.Modules[module] = module_class(self)

		print('[App]: Modules loaded')

	def init_caps(self):
		for cam_id in self.Cams:
			self.Caps[cam_id] = Cap(self, self.Cams[cam_id])

		print('[App]: Caps loaded')

