import cherrypy
from datetime import datetime, timedelta
from cherrypy.process import plugins

def GMT(t):
    # G = timezone("GMT")
    # utc = t.utcnow()
    t += timedelta(hours=8)
    fmt = '%Y / %m / %d %H:%M'
    return t.strftime(fmt)

class FilePlugin(plugins.SimplePlugin):
    def __init__(self, bus, downloadpath):
        plugins.SimplePlugin.__init__(self, bus)
        self.files = {}
        self.users_files = {}
        self.dl_path = downloadpath

    def __getitem__(self, i):
        return self.users_files[i]

    def start(self):
        with open("file_record.txt") as file:
            files = file.read().split("\n")
        for file in files:
            if file == "":
                continue

            filename, updated_time, lastupdate = file.split(",")
            self.users_files[filename] = {
                "updated_time": int(updated_time),
                "lastupdate": lastupdate,
                }

    def stop(self):
        with open("file_record.txt", "w") as file:
            for filename, fileinfo in self.users_files.items():
                txt = f"{filename},{fileinfo['updated_time']},{fileinfo['lastupdate']}"
                file.write(txt)

    def write_file_from_file(self, filename, file):
        f = open(filename, "wb")
        while True:
            data = file.file.read(8192)
            if not data:
                break
            f.write(data)
        f.close()

        if filename in self.users_files:
            self.users_files[filename]["updated_time"] += 1
        else:
            self.users_files[filename] = {
            "updated_time": 1,
            "lastupdate": GMT(datetime.utcnow()),
            }

    def write_sys_file(self, filename, data):
        try:
            with open(self.dl_path + filename, "w") as file:
                file.write(data)
            self.files[filename] = data
            return True
        except:
            return False

    def read_sys_file(self, filename):
        try:
            if filename not in self.files:
                with open(self.dl_path + filename, "r") as file:
                    read = file.read()
                self.files[filename] = read
                return read
            else:
                return self.files[filename]
        except:
            return False

    def get_download_path(self):
        return self.dl_path

class FileTool(cherrypy.Tool):
    def __init__(self, fileplugin):
        cherrypy.Tool.__init__(self, "on_start_resource",
            self.get_class_mgr,
            priority=10)
        self.fileplugin = fileplugin

    def get_plugin(self):
        return self.fileplugin

    def get_class_mgr(self):
        cherrypy.request.file_mgr = self.fileplugin
