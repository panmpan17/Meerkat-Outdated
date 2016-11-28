import cherrypy
from cherrypy.process import plugins

class ClassesPlugin(plugins.SimplePlugin):
	def __init__(self, bus, downloadpath):
		plugins.SimplePlugin.__init__(self, bus)
		self.classes = {}
		self.dl_path = downloadpath

	def start(self):
		pass

	def stop(self):
		pass

	def new_class(self, class_id, classinfo):
		self.classes[class_id] = classinfo

	def get_class(self, class_id):
		if class_id not in self.classes:
			return False
		return self.classes[class_id]

	def get_subject_name(self, class_id):
		if class_id not in self.classes:
			return False
		return self.classes[class_id]["subject"]

	def get_class_all_info(self):
		classes_json = []
		v = ["hourofcode", "scratch_1", "teacher_1", "python_01"]
		for c in v:
			j = {
				"subject": self.classes[c]["subject"],
				"time": self.classes[c]["time"],
				"price": self.classes[c]["price"],
				"summary": self.classes[c]["summary"],
				"image": self.classes[c]["image"],
				"description": self.classes[c]["description"],
				"id": self.classes[c]["id"],
				}
			classes_json.append(j)
		return classes_json

	def get_classes_name(self):
		return self.classes.keys()

	def get_download_path(self):
		return self.dl_path

class ClassesTool(cherrypy.Tool):
	def __init__(self, classes_plugin):
		cherrypy.Tool.__init__(self, "on_start_resource",
			self.get_class_mgr,
			priority=10)
		self.classes_plugin = classes_plugin

	def get_plugin(self):
		return self.class_plugin

	def get_class_mgr(self):
		cherrypy.request.classes = self.classes_plugin
