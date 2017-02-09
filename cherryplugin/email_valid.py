import cherrypy
from cherrypy.process import plugins
from datetime import datetime
from uuid import uuid1

MINUTE = 60
HOUR = 60
DAY = 24
KEYTIMEOUT = 2 * DAY * HOUR * MINUTE

class EmailValidPlugin(plugins.SimplePlugin):
	def __init__(self, bus):
		plugins.SimplePlugin.__init__(self, bus)
		self.validdict = {}

	def start(self):
		pass
	def stop(self):
		pass

	def new_mail(self, uid):
		key = str(uuid1())
		self.validdict[uid] = {
			"key": key,
			"datetime": datetime.now(),
			}
		return key

	def check_mail(self, uid, key):
		value = self.validdict.get(uid)
		if value:
			if self.validdict[uid]["key"] == key:
				timedelta = datetime.now() - self.validdict[uid]["datetime"]
				self.validdict.pop(uid)
				if timedelta.seconds < KEYTIMEOUT:
					return True
		else:
			pass
		return False

class EmailValidTool(cherrypy.Tool):
	def __init__(self, email_valid_plugin):
		cherrypy.Tool.__init__(self, "on_start_resource",
			self.get_email_valid, priority=10)
		self.email_valid_plugin = email_valid_plugin

	def get_plugin(self):
		return sef.email_valid_plugin

	def get_email_valid(self):
		cherrypy.request.email_valid = self.email_valid_plugin