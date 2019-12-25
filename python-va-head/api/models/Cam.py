
class Cam:
	"""docstring for Cam"""
	def __init__(self, rid):
		self.rid = rid
		self.state = {}
		
	def load(self, state):
		self.state = state

	def get(self, field):
		return self.state[field]

	def getId(self):
		return self.rid

	def getSettings(self, module):
		return self.state['settings'][module]
