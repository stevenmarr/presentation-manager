#error.py

from mainh import BaseHandler

class NotFoundPageHandler(BaseHandler):
    def get(self):
        self.error(404)
        self.render_response('404.html')