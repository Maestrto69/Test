import requests
import json


endpoint = 'http://localhost:80/api'

class APIHelper():
	"""Работает с базой данных"""
	def __init__(self, api_ver):
		self.api_ver = api_ver
		
	def getEndpoint(self, namespace, method):
		return '/'.join([endpoint, 'v' + self.api_ver, namespace, method])
	
	def fetchAll(self, namespace): 
		page = requests.get(self.getEndpoint(namespace, 'find.all'))
		dat = page.json()
		return dat

	def count(self, namespace):
		page = requests.get(self.getEndpoint(namespace, 'count'))
		dat = page.json()
		return dat['count']

	def findVector(self, face_vect):
		page = requests.post('http://localhost:80/facedetection/v1/face_models/find.vector', face_vect)
		#print("page = ", page)
		dat = page.json()
		return dat

	def findModulesByCam_id(self, _id):
		page = requests.get(self.getEndpoint("module_settings/find.camid", _id))
		dat = page.json()
		return dat["records"]

	def findModuleByMod_id(self, _id):
		page = requests.get(self.getEndpoint("modules/find.id", _id))
		dat = page.json()
		return dat["records"]



	def removeId(self,namespace, id):
		page = requests.post(self.getEndpoint(namespace, 'remove.id/' + id))
		return page.json()

	def removeAll(self,namespace):
		page = requests.post(self.getEndpoint(namespace, 'remove.all/'))
		return page.json()
	

	def create(self, namespace, body):
		page = requests.post(self.getEndpoint(namespace, 'add'), body)
		return page.json()

	def update(self, namespace, params):
		page = requests.get(self.getEndpoint(namespace, 'update/' + params.id), params.body)
		return page.json()
