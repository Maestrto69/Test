import cv2
import time
import urllib.request
import socketio
import numpy as np

from threading import Thread

from api.models.Cam import Cam
from cap.Cap import Cap

class Sockets:
	"""docstring for Sockets"""
	def __init__(self, app):
		self.App = app
		self.Client = socketio.Client(reconnection=True)

		self.init_handlers()
		self.Thread = Thread(target=self.connect).start()

	def init_handlers(self):
		self.Client.on('connect', self.on_connect)
		self.Client.on('disconnect', self.on_disconnect)
		self.Client.on('orm', self.on_orm)

	def connect(self):
		# try:
		# 	self.Client.connect(self.App.Config.sockets_endpoint)
		# except Exception as e:
		# 	print('[Sockets]: Connection refused, retry.. (theard blocked)')
		# 	time.sleep(self.App.Config.sockets_reconnect_sleep)
		# 	self.connect()
		while True:
			try:
				self.Client.connect(self.App.Config.sockets_endpoint)

				if self.Client.eio.state != 'connected':
					print('[Sockets][eio-status]: Connection aborted, retry.. (theard blocked)')
					self.Client.disconnect()
					self.Client.connect(self.App.Config.sockets_endpoint)
					time.sleep(self.App.Config.sockets_reconnect_sleep)
			except Exception as e:
				print('[Sockets][exception]: Connection refused, retry.. (theard blocked)')
				time.sleep(self.App.Config.sockets_reconnect_sleep)
			
			time.sleep(self.App.Config.sockets_reconnect_sleep)

	def on_connect(self):
		print('[Sockets]: Connection established')

	def on_disconnect(self):
		print('[Sockets]: Disconnected from server')

	def on_orm(self, data):
		if data['type'] == 'Cams':
			if data['operation'] == 'remove':
				for rid in data['ids']:
					self.App.Caps[rid].is_run = False
					self.App.Caps[rid].Thread.join()
					self.App.Caps.pop(rid, None)
					self.App.Cams.pop(rid, None)
					self.App.FrameHandler.run_dvr[rid].release()
					print('[Sockets][ORM][Cams]: removed %s' % rid)
			if data['operation'] == 'update':
				for rid in data['ids']:
					# self.App.Caps.pop(rid, None)
					# self.App.Caps[rid].Thread.join()
					self.App.Cams[rid].load(data['record'])
					self.App.Caps[rid] = Cap(self.App, self.App.Cams[rid])
					print('[Sockets][ORM][Cams]: updated %s' % rid)
			if data['operation'] == 'create':
				for rid in data['ids']:
					self.App.Cams[rid] = Cam(rid)
					self.App.Cams[rid].load(data['record'])
					self.App.Caps[rid] = Cap(self.App, self.App.Cams[rid])
					print('[Sockets][ORM][Cams]: created %s' % rid)
		if data['type'] == 'Humans':
			if data['operation'] == 'add_media':
				for rid in data['ids']:
					if 'face_identification' in self.App.Modules:
						image_url = "/".join(['http:/', data['record']['cdn_public_url'], data['record']['cdn_id']])

						resp = urllib.request.urlopen(image_url)
						image = np.asarray(bytearray(resp.read()), dtype="uint8")
						image = cv2.imdecode(image, cv2.IMREAD_COLOR)

						self.App.Modules['face_identification'].add_facemodel(rid, data['record']['id'], image)

						print('[Sockets][ORM][Humans]: add_media %s' % rid)
					#
				#
			#
		#