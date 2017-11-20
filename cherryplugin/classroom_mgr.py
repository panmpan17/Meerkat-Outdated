import cherrypy
import os
from datetime import datetime
from cherrypy.process import plugins

class ClassroomMgrPlugin(plugins.SimplePlugin):
    def __init__(self, bus, path):
        plugins.SimplePlugin.__init__(self, bus)
        self.cls_per_key = {}
        self.forms = {}
        self.file = {}
        self.path = path

    def start(self):
        self.bus.log("Starting Classroom Manager")

        for folder in os.listdir(self.path):
            path = f"{self.path}{folder}/form/"
            if os.path.isdir(path):
                files = os.listdir(path)

                classroom = {}
                for file in files:
                    userid = int(file.replace(".txt", ""))
                    classroom[userid] = {}
                    with open(path + file) as file:
                        read = file.read()

                    forms = read.split("\n")
                    try:
                        forms.remove("")
                    except:
                        pass

                    for form in forms:
                        title, answers = form.split("|")
                        answers = answers.split(",")
                        classroom[userid][title] = answers
                self.forms[folder] = classroom
        print(self.forms)

    def stop(self):
        self.bus.log("Closing Classroom Manager")

        for folder, classroom in self.forms.items():
            path = f"{self.path}/{folder}/form/"
            for id_, questions in classroom.items():
                filename = path + f"{id_}.txt"

                txt = []
                for question, answers in questions.items():
                    txt.append(f"{question}|" + ",".join(answers))

                with open(filename, "w") as file:
                    file.write("\n".join(txt))

    def get_cls_per_key(self, key):
        try:
            return self.cls_per_key[key]
        except:
            return False

    def update_cls_per_key(self, key, key_type, clsr_id):
        self.cls_per_key[key] = {
            "date": datetime.now(),
            "type": key_type,
            "clsr_id": clsr_id
            }

    def new_answer(self, folder, student_id, form, answer):
        print(self.forms)
        if folder not in self.forms:
            self.forms[folder] = {}
        if student_id not in self.forms[folder]:
            self.forms[folder][student_id] = {}
        if form not in self.forms[folder][student_id]:
            self.forms[folder][student_id][form] = []

        self.forms[folder][student_id][form].append(answer)
        print(self.forms)

    def get_classroom(self, folder):
        if folder in self.forms:
            return self.forms[folder]
        return {}

class ClassroomMgrTool(cherrypy.Tool):
    def __init__(self, clsrom_plugin):
        cherrypy.Tool.__init__(self, "on_start_resource",
            self.get_classroom_mgr, priority=10)
        self.clsrom_plugin = clsrom_plugin

    def get_plugin(self):
        return self.clsrom_plugin

    def get_classroom_mgr(self):
        cherrypy.request.clsrom = self.clsrom_plugin
