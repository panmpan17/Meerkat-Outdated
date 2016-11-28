from contextlib import contextmanager

@contextmanager
def dbss_ctx(dbss_cls):
    ss = dbss_cls()
    try:
        yield ss
        ss.commit()
    except:
        ss.rollback()
    finally:
        ss.close()

@contextmanager
def safe_json(att):
    try:
        yield att
    except AttributeError:
        raise cherrypy.HTTPError(400, ParamErrors.NEED_JSON)

#
# The plugin of sqlalchemy DB. Started when bus start...
# 
import cherrypy
from cherrypy.process import wspbus, plugins
from sqlalchemy import create_engine, MetaData
#from sqlalchemy.orm import scoped_session, sessionmaker

class SAPlugin(plugins.SimplePlugin):
    def __init__(self, bus, db_str=None, tables=[]):
        """
        The plugin is registered to the CherryPy engine and therefore
        is part of the bus (the engine *is* a bus) registery.
 
        We use this plugin to create the SA engine. At the same time,
        when the plugin starts we create the tables into the database
        using the mapped class of the global metadata.
        """
        plugins.SimplePlugin.__init__(self, bus)
        self.sa_engine = self.sa_meta = None
        self.sa_connstr = db_str
        self.tables = tables
 
    def start(self):
        self.bus.log('Starting up DB access')
        if self.sa_connstr == "sqlite:///:memory:" or self.sa_connstr == "sqlite://":
            from sqlalchemy.pool import StaticPool
            self.bus.log('create memory db')
            self.sa_engine = create_engine(self.sa_connstr, connect_args={'check_same_thread':False},
                poolclass=StaticPool)
        else:
            self.sa_engine = create_engine(self.sa_connstr, echo=False)
        self.sa_meta = MetaData()
        #for p, a in cherrypy.tree.apps.items():
        #    if hasattr(a.root, "create_schema"):
        #        a.root.create_schema(self.sa_engine, self.sa_meta)
        for t in self.tables:
            if isinstance(t, tuple):
                t[0].create_schema(self.sa_engine, self.sa_meta, euf=t[1])
                continue
            t.create_schema(self.sa_engine, self.sa_meta)


    def get_meta_conn(self):
        return self.sa_meta, self.sa_engine.connect()

    def stop(self):
        self.bus.log('Stopping down DB access')
        if self.sa_engine:
            self.sa_engine.dispose()
            self.sa_engine = None

class SATool(cherrypy.Tool):
    def __init__(self, sa_plugin):
        """
        The SA tool is responsible for associating a SA session
        to the SA engine and attaching it to the current request.
        Since we are running in a multithreaded application,
        we use the scoped_session that will create a session
        on a per thread basis so that you don't worry about
        concurrency on the session object itself.
 
        This tools binds a session to the engine each time
        a requests star,ts and commits/rollbacks whenever
        the request terminates.
        """
        cherrypy.Tool.__init__(self, 'on_start_resource',
                               self.bind_connection,
                               priority=10)
        self.sa_plugin = sa_plugin

    def _setup(self):
        cherrypy.Tool._setup(self)
        cherrypy.request.hooks.attach('on_end_request',
                                      self.close_connection,
                                      priority=80)

    def get_plugin(self):
        return self.sa_plugin
 
    def bind_connection(self):
        """
        Attaches a session to the request's scope by requesting
        the SA plugin to bind a session to the SA engine.
        """
        #self.sa_plugin.bus.log("bind connection, r={}".format(id(cherrypy.request)))
        cherrypy.request.db = self.sa_plugin.get_meta_conn()
 
    def close_connection(self):
        """
        Commits the current transaction or rolls back
        if an error occurs. Removes the session handle
        from the request's scope.
        """
        if not hasattr(cherrypy.request, 'db'):
            return
        #self.sa_plugin.bus.log("close connection, r={}".format(id(cherrypy.request)))
        cherrypy.request.db[1].close() #close the db connection
