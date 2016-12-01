import cherrypy
from cherrypy.process import plugins

import smtplib
from queue import Queue
import _thread

class EmailPlugin(plugins.SimplePlugin):
	def __init__(self, bus,
		usrn="coding4fun.tw@gmail.com", psw="shalley1702OK"):
		plugins.SimplePlugin.__init__(self, bus)
		self.usrn = usrn
		self.psw = psw

		self.queue = Queue()

	def start(self):
		self.server = smtplib.SMTP('smtp.gmail.com')
		self.server.ehlo()
		self.server.starttls()
		self.server.ehlo()

		self.server.login(self.usrn, self.psw)
		self.bus.log("Gmail Login '{}'".format(self.usrn))

	def stop(self):
		self.server.quit()

	def put(self, addr, subject, content):
		self.queue.put((addr, subject, content))

	def send(self):
		addr, subject, content = self.queue.get()
		smtpformat = EmailPlugin.format_mail(addr, subject, content)

		self.server.sendmail(self.usrn, addr, smtpformat)

	@staticmethod
	def format_mail(addr, subject, content):
		f = """From: Coding for Fun <coding4fun.tw@gmail.com>
			To: {addr} <{addr}>
			Subject: {subject}
			MIME-Version: 1.0
			Content-Type: text/html
			Content-Transfer-Encoding:8bit

			{content}
			"""
		f = f.replace("\t", "")
		f = f.format(subject=subject, content=content, addr=addr)
		return f.encode("utf-8")


class EmailTool(cherrypy.Tool):
	def __init__(self, email_plugin):
		cherrypy.Tool.__init__(self, "on_start_resource",
			self.get_email_mgr,
			priority= 10)
		self.email_plugin = email_plugin
		_thread.start_new_thread(self.sendqueue, ())

	def get_plugin(self):
		return self.email_plugin

	def get_email_mgr(self):
		cherrypy.request.email = self.email_plugin

	def sendqueue(self):
		while True:
			self.email_plugin.send()

