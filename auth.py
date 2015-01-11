import sys
sys.path.insert(0, 'lib') #"Old" way, not working for me.
from dropbox.client import DropboxOAuth2Flow, DropboxClient
import webapp2



access_token, user_id, url_state = DropboxOAuth2Flow.finish(request.get)
redirect_to('http://localhost:9088/')
