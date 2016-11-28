import cherrypy
from cherrypy.process import plugins

class EmailPlugin(plugins.SimplePlugin):
	def __init__(self, bus, usrn, psw):
		plugins.SimplePlugin.__init__(self, bus)
		self.user = (usrn, psw)

	def start(self):
		self.bus.log("Gmail Login %s, %s" % self.user)

	def stop(self):
		pass

class EmailTool(cherrypy.Tool):
	def __init__(self, email_plugin):
		cherrypy.Tool.__init__(self, "on_start_resource",
			self.get_email_mgr,
			priority= 10)
		self.email_plugin = email_plugin

	def get_plugin(self):
		return self.email_plugin

	def get_email_mgr(self):
		cherrypy.request.email = self.email_plugin

