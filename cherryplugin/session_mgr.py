import cherrypy
from cherrypy.process import plugins
from datetime import datetime
from time import sleep
import _thread

MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY
KEYTIMEOUT = WEEK #become seconds

class KeyMgrPlugin(plugins.SimplePlugin):
	def __init__(self, bus):
		plugins.SimplePlugin.__init__(self, bus)
		self.keydict = {}

	def start(self):
		pass
	def stop(self):
		pass

	def get_key(self, key):
		value = self.keydict.get(key)
		if value:
			timedelta = datetime.now() - value["datetime"]
			if timedelta.seconds < KEYTIMEOUT:
				value["datetime"] = datetime.now()
				return (True, value["requester"])
			else:
				self.keydict.pop(key)
				return (False, "timeout")
		else:
			return (False, "wrong")

	def update_key(self, key, requester):
		self.keydict[key] = {
			"datetime": datetime.now(),
			"requester": requester,
			}

class KeyMgrTool(cherrypy.Tool):
	def __init__(self, key_plugin):
		cherrypy.Tool.__init__(self, "on_start_resource",
			self.get_key_mgr, priority=10)
		self.key_plugin = key_plugin
		_thread.start_new_thread(self.delete_key, ())

	def get_plugin(self):
		return self.key_plugin

	def get_key_mgr(self):
		cherrypy.request.key = self.key_plugin

	def delete_key(self):
		while True:
			sleep(DAY)
			keys = []
			now = datetime.now()
			for i in self.key_plugin.keydict:
				timedelta = now - self.key_plugin.keydict[i]["datetime"]

				if timedelta.seconds > KEYTIMEOUT:
					keys.append(i)

			if keys == []:
				print("No key been delete")
			else:
				for i in keys:
					self.key_plugin.keydict.pop(i)
					print("Key '{}' been delete".format(i))