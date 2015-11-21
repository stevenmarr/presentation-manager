from main import BaseHandler, config
import webapp2
import urllib
import urllib2
import secrets
import logging

class StartOauthHandler(BaseHandler):
  def get(self):
    query_args = {  'response_type':'code', 
                    'client_id':secrets.App_key,
                    'redirect_uri':'https://presetationmgr.appspot.com/oauth2',
                    #'redirect_uri':'http://localhost:8080/oauth2',
                    'state':"",
                    'force_reapprove':'false',
                    'disable_signup':'true' }
    encoded_args = urllib.urlencode(query_args)
    #url = 'https://www.dropbox.com/1/oauth2/authorize'+'?'+ encoded_args                
    url = 'https://www.dropbox.com/1/oauth2/authorize'+'?'+encoded_args
    self.redirect(url)
    
    #request = urllib2.Request(url)
    #handler = urllib2.urlopen(request)
    
class DBResponseHandler(BaseHandler):
    def get(self):
        code = self.request.get('code')
        logging.error('code %s' % code)
        url = "https://api.dropbox.com/1/oauth2/token"
        #url = 'http://localhost:8080/'
        params = { 'code':code,
                        'grant_type': 'authorization_code',
                        'client_id': secrets.App_key,
                        'client_secret': secrets.App_secret,
                        'redirect_uri':'https://presetationmgr.appspot.com/oauth2'}
                        #'redirect_uri':'http://localhost:8080/oauth2'}
        data = urllib.urlencode(params)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        this_page = response.read()     
        
        logging.error("request for request data is  %s"% this_page)
       
    
        

app = webapp2.WSGIApplication([
  webapp2.Route('/oauth2/init',     StartOauthHandler),
       ('/oauth2#.*',                      DBResponseHandler),
       ('/oauth2/',                      DBResponseHandler),
      webapp2.Route ('/oauth2',                      DBResponseHandler),
       webapp2.Route('/oauth2/',                      DBResponseHandler),
      webapp2.Route('/oauth2/init',     StartOauthHandler)
    
], debug=True, config=config)