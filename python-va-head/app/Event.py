import cv2
import pybase64
import requests

class EventLevel:
	Log = 'log'
	Warn = 'warn'
	Alert = 'alert'


class Event:
	"""docstring for Event"""
	static_app = None

	@staticmethod
	def create_record(namespace, body):
		try:
			res = requests.post("/".join(
				[Event.static_app.Config.api_endpoint, Event.static_app.Config.api_version,
				 namespace, 'add']), body)

			if res.status_code == 200:
				res_json = res.json()
				return res_json
			else:
				return None
		except Exception as e:
			return None

	@staticmethod
	def create_event(frame, event_type, title, message, cam_id):
		media = Event.create_record('medias',
								   {'name': 'c1_2-screenshot-event-od'})

		# print('NEW MEDIA: %s' % json.dumps(media))
		media_id = media["id"]
		media_url = "/".join(
			['http:/', media['cdn_public_url'], media['cdn_id']])
		imencoded = \
		cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 20])[1]
		files = {'media': imencoded.tostring()}
		requests.post(media_url, files=files)

		# print('MEDIA URL: %s' % media_url)
		# event_link_medias = { 'screenshot_id':  media_id }
		# event_link = { 'cam_id': cam_id, 'medias': event_link_medias }

		event_body = {'module_name': 'face_identification',
					  'media_url': media_url, 'type': event_type,
					  'title': title, 'message': message, 'cam_id': cam_id,
					  'screenshot_id': media_id}

		# print("NEW EVENT BODY: %s" % json.dumps(event_body))
		event = Event.create_record('events', event_body)
		return event

	def __init__(self, app):
		self.App = app
		Event.static_app = app

	def emit_event(self, event, frame):
		encoded, buffer = cv2.imencode('.jpg', frame.frame, [int(cv2.IMWRITE_JPEG_QUALITY), 20])
		base64_frame = pybase64.standard_b64encode(buffer)

		self.App.Sockets.Client.emit('event', { 'cam_id': frame.Cam.getId(), 'body': event, 'frame': base64_frame })

	def emit_frame(self, drawn_frame, cam):
		encoded, buffer = cv2.imencode('.jpg', drawn_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 20])
		base64_frame = pybase64.standard_b64encode(buffer)

		self.App.Sockets.Client.emit('frame', { 'cam_id': cam.getId(), 'body': base64_frame })
