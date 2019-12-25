import cv2
import json
import requests
import pybase64
import tensorflow as tf
from app.Event import Event, EventLevel
from collections import deque

from drawer.DrawScript import DrawScript, Label

class fire_detector:
	"""docstring for fire_detector"""
	def __init__(self, app):
		self.App = app
		print('[Module][fire_detector]: Init')

		# TODO: добавить параметр размера буфера в настройки модуля
		# self.scores_buffer = deque([], 10)
		self.scores_buffers = {}

		graphs_folder_name = 'modules/fire_detector'
		graph_postfix = 'trained_graph.pb'
		labels_postfix_en = 'trained_labels.txt'

		label_path = "{}/{}".format(graphs_folder_name, labels_postfix_en)
		self.label_lines = [line.rstrip() for line in tf.gfile.GFile(label_path)]

		graph_path = "{}/{}".format(graphs_folder_name,graph_postfix)
		with tf.gfile.FastGFile(graph_path, 'rb') as f:
			graph_def = tf.GraphDef()
			graph_def.ParseFromString(f.read())
			tf.import_graph_def(graph_def, name='')

		config = tf.ConfigProto()
		config.gpu_options.per_process_gpu_memory_fraction = 0.1
		
		self.sess = tf.Session(config=config)

		# Feed the image_data as input to the graph and get first prediction
		self.softmax_tensor = self.sess.graph.get_tensor_by_name('final_result:0')

	"""def createRecord(self, namespace, body):
		try:
			res = requests.post("/".join(['http://localhost:81/api/v1', namespace, 'add']), body)

			if res.status_code == 200:
				res_json = res.json()
				return res_json
			else:
				return None
		except Exception as e:
			return None

	def create_event(self, frame, event_type, title, message, cam_id):

		media = self.createRecord('medias', { 'name': 'c1_2-screenshot-event-od' })

		# print('NEW MEDIA: %s' % json.dumps(media))

		media_id = media["id"]

		media_url = "/".join(['http:/', media['cdn_public_url'], media['cdn_id']])

		imencoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 20])[1]

		files = { 'media': imencoded.tostring() }
		requests.post(media_url, files=files)

		# print('MEDIA URL: %s' % media_url)

		# event_link_medias = { 'screenshot_id':  media_id }

		# event_link = { 'cam_id': cam_id, 'medias': event_link_medias }

		event_body = { 'module_name': 'object_detector', 'media_url': media_url, 'type': event_type, 'title': title, 'message': message, 'cam_id': cam_id, 'screenshot_id':  media_id }
		

		# print("NEW EVENT BODY: %s" % json.dumps(event_body))

		event = self.createRecord('events', event_body)

		return event"""

	def process(self, frame):
		raw_frame = frame.frame
		module_settings = frame.Cam.getSettings('fire_detector')

		draw_script = DrawScript(module_settings['draw_settings'])

		# confidence_level
		confidence_level = module_settings['confidence']

		image_data = cv2.imencode('.jpg', raw_frame)[1].tostring()

		predictions = self.sess.run(self.softmax_tensor, {'DecodeJpeg/contents:0': image_data})

		# Sort to show labels of fire_detectorst prediction in order of confidence
		top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
		human_string = [None,None]
		score = [None, None]

		for node_id in top_k:
			human_string[node_id] = self.label_lines[node_id]
			score[node_id] = predictions[0][node_id]

		if frame.Cam.getId() not in self.scores_buffers:
			self.scores_buffers[frame.Cam.getId()] = deque([], 10)
		buf = self.scores_buffers[frame.Cam.getId()]
		buf.appendleft(score[1])
		confidence = sum(buf) / len(buf)

		if confidence > module_settings['confidence']:
			Event.create_event(raw_frame, EventLevel.Alert,
					frame.Cam.get('title') + ': детектор огня',
					'Зафиксирован источник открытого огня', frame.Cam.getId())

		if module_settings['draw_confid'] == 1:
			if confidence > module_settings['confidence']:
				label = "FIRE! {}%".format(str(round(score[1] * 100, 2)))
				draw_script.add_label(Label(label, (200, 250), color=(0, 69, 255),
						line_thickness=13, font_size=4))

		return draw_script
