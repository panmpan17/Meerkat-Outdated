import cherrypy
from cherrypy.process import plugins

class ClassesPlugin(plugins.SimplePlugin):
	def __init__(self, bus):
		plugins.SimplePlugin.__init__(self, bus)
		self.classes = {}
		self.videos = {}
		self.files = {}
		self.evaluations = {}

	def start(self):
		pass

	def stop(self):
		pass

	def new_class(self, class_id, classinfo):
		self.classes[class_id] = classinfo
		self.classes[class_id]["lesson_length"] = {}
		self.classes[class_id]["title"] = []

		for i, lesson in enumerate(classinfo["lessons"]):
			self.classes[class_id]["lesson_length"][i] = len(lesson["content"])

			hided = False
			if "hide" in lesson:
				hided = lesson["hide"]

			self.classes[class_id]["title"].append({
				"title": lesson["title"],
				"hide": hided,
				})

		evaluations = {}
		for lesson in classinfo["lessons"]:
			for content in lesson["content"]:
				if content["type"] == "evaluation":
					evaluations[content["class_name"]] = content
		self.evaluations[class_id] = evaluations

	def video_find_class(self, videourl):
		for class_id in self.videos:
			try:
				return self.videos[class_id][videourl], class_id
			except:
				pass
		return None

	def get_class(self, class_id):
		if class_id not in self.classes:
			return False
		return self.classes[class_id]

	def get_subject_name(self, class_id):
		if class_id not in self.classes:
			return False
		return self.classes[class_id]["subject"]

	def get_subjects_name(self):
		return tuple(self.classes.keys())

	def get_class_all_info(self):
		classes_json = []
		v = ["scratch_1", "python_01", "scratch_02"]
		for c in v:
			j = {
				"subject": self.classes[c]["subject"],
				# "time": self.classes[c]["time"],
				"permission": self.classes[c]["permission"],
				"summary": self.classes[c]["summary"],
				"style": self.classes[c]["style"],
				"id": self.classes[c]["id"],
				"trial": self.classes[c]["trial"],
				}
			classes_json.append(j)
		return classes_json

	def get_classes_name(self):
		return self.classes.keys()

	def get_evals(self, type_):
		if type_ not in self.evaluations:
			return None
		return self.evaluations[type_]

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
