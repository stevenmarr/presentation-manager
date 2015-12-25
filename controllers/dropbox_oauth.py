from mainh import BaseHandler
import webapp2
import urllib
import urllib2

import logging

from config.secrets import APP_KEY, APP_SECRET

log = logging.getLogger(__name__)


class StartOauthHandler(BaseHandler):
  def get(self):
    query_args = {  'response_type':'code', 
                    'client_id':APP_KEY,
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
                        'client_id': APP_KEY,
                        'client_secret': APP_SECRET,
                        'redirect_uri':'https://presetationmgr.appspot.com/oauth2'}
                        #'redirect_uri':'http://localhost:8080/oauth2'}
        data = urllib.urlencode(params)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        this_page = response.read()     
        
        logging.error("request for request data is  %s"% this_page)
       