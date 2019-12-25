import json
import requests

class Api:
	"""docstring for API"""
	def __init__(self, app):
		self.App = app

	def findAll(self, namespace):
		try:
			res = requests.get("/".join([self.App.Config.api_endpoint, self.App.Config.api_version, namespace, 'find.all']))

			if res.status_code == 200:
				res_json = res.json()
				
				if res_json['count'] > 0:
					return res_json['records']
				else:
					return None
			else:
				return None
		except Exception as e:
			return None
	
	def findById(self, namespace, rid):
		res = requests.get("/".join([self.App.Config.api_endpoint, self.App.Config.api_version, namespace, 'find.id', rid]))
		return res.json()

	def findFaceByVector(self, face_vect):
		res = requests.post(self.App.Config.facedetection_endpoint + '/v1/face_models/find.vector', face_vect)
		return res.json()

	def create(self, namespace, body):
		res = requests.post("/".join([self.App.Config.api_endpoint, self.App.Config.api_version, namespace, 'add']), body)
		return res.json()