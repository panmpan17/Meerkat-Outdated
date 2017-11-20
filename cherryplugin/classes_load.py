import cherrypy
from cherrypy.process import plugins

class ClassesPlugin(plugins.SimplePlugin):
	def __init__(self, bus):
		plugins.SimplePlugin.__init__(self, bus)
		self.classes = {}
		self.videos = {}
		self.files = {}
		self.form_answers = {}

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
			self.classes[class_id]["title"].append(lesson["title"])

		form_answer = {}
		for lesson in classinfo["lessons"]:
			for content in lesson["content"]:
				if content["type"] == "evaluation":
					answer = []
					for question in content["questions"]:
						q_a = [str(i) for i in question["answer"]]
						answer.append("".join(q_a))
					form_answer[content["class_name"]] = "a".join(answer)
		self.form_answers[class_id] = form_answer


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

	def get_class_all_info(self):
		classes_json = []
		v = ["scratch_1", "teacher_1", "python_01"]
		for c in v:
			j = {
				"subject": self.classes[c]["subject"],
				"time": self.classes[c]["time"],
				"permission": self.classes[c]["permission"],
				"summary": self.classes[c]["summary"],
				"description": self.classes[c]["description"],
				"style": self.classes[c]["style"],
				"id": self.classes[c]["id"],
				}
			classes_json.append(j)
		return classes_json

	def get_classes_name(self):
		return self.classes.keys()

	def get_answer(self, type_):
		if type_ not in self.form_answers:
			return None
		return self.form_answers[type_]

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
