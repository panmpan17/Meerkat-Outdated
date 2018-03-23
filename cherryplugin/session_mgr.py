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
        # self.keydict = {"0fc467ca-2e64-11e8-a139-28cfe91c3f5f": {
        #     "date": datetime.utcnow(),
        #     "requester": "1",
        #     }}

        self.cls_per = {}
        self.cls_per_key = self.cls_per.keys()

    def start(self):
        pass
    def stop(self):
        pass

    def get_key(self, key):
        value = self.keydict.get(key)
        if value != None:
            timedelta = datetime.utcnow() - value["date"]
            if timedelta.seconds < KEYTIMEOUT:
                value["date"] = datetime.utcnow()
                return (True, value["requester"])
            else:
                self.keydict.pop(key)
                return (False, "timeout")
        else:
            return (False, "wrong")

    def update_key(self, key, requester):
        self.keydict[key] = {
            "date": datetime.utcnow(),
            "requester": requester,
            }

    def drop_key(self, key):
        self.keydict.pop(key)

    def get_cls_per_key(self, key):
        try:
            return self.cls_per_key[key]
        except:
            return False

    def update_cls_per_key(self, key, key_type, clsr_id):
        self.cls_per[key] = {
            "date": datetime.utcnow(),
            "type": key_type,
            "clsr_id": clsr_id
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
            print('start key cleaning')
            keys = []
            utcnow = datetime.utcnow()
            for k, i in self.key_plugin.keydict.items():
                timedelta = utcnow - i["date"]

                if timedelta.seconds > KEYTIMEOUT:
                    keys.append(k)

            for i in keys:
                print(self.key_plugin.keydict)
                self.key_plugin.keydict.pop(i)
                print(f"Key {i} been delete")

            keys = []
            for k, i in self.key_plugin.cls_per.items():
                timedelta = utcnow - i["date"]

                if timedelta.seconds > 2 * HOUR:
                    keys.append(k)

            for i in keys:
                self.key_plugin.cls_per.pop(i)
                print(f"Class Permission Key {i} been delete")
