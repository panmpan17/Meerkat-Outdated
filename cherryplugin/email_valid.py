import cherrypy
import re
from cherrypy.process import plugins
from datetime import datetime
from uuid import uuid1 as uuid

MINUTE = 60
KEYTIMEOUT = 15 * MINUTE

def generate_code():
	code = str(uuid())
	code_pat = code.split("-")
	code = ""
	for i in code_pat:
		numbers = re.findall("[0-9]", i)
		code += str(len(numbers))
	return str(code)

class ChangeEmail:
	def __init__(self, old):
		self.old = old
		self.code = generate_code()
		self.new = None
		self.stage = 1

	def newcode(self):
		self.code = generate_code()

class EmailValidPlugin(plugins.SimplePlugin):
	def __init__(self, bus):
		plugins.SimplePlugin.__init__(self, bus)
		self.validdict = {}
		self.changeemails = {}

	def start(self):
		pass
	def stop(self):
		pass

	def new_mail(self, uid):
		key = generate_code()
		self.validdict[uid] = {
			"key": key,
			"datetime": datetime.utcnow(),
			}
		return key

	def get_status(self, uid):
		try:
			timedelta = datetime.utcnow() - self.validdict[uid]["datetime"]
			return timedelta.seconds < KEYTIMEOUT
		except Exception as e:
			return False

	def check_mail(self, uid, key):
		value = self.validdict.get(uid)
		if value:
			if self.validdict[uid]["key"] == key:
				timedelta = datetime.utcnow() - self.validdict[uid]["datetime"]
				self.validdict.pop(uid)
				if timedelta.seconds < KEYTIMEOUT:
					return True
		return False

	def new_change(self, uid, email):
		self.changeemails[uid] = ChangeEmail(email)

		return self.changeemails[uid].code

	def delete_change(self, uid):
		self.changeemails.pop(uid)

class EmailValidTool(cherrypy.Tool):
	def __init__(self, email_valid_plugin):
		cherrypy.Tool.__init__(self, "on_start_resource",
			self.get_email_valid, priority=10)
		self.email_valid_plugin = email_valid_plugin

	def get_plugin(self):
		return sef.email_valid_plugin

	def get_email_valid(self):
		cherrypy.request.email_valid = self.email_valid_plugin