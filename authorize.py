from dropbox.client import DropboxOAuth2Flow, DropboxClient
import webapp2

access_token, user_id, url_state = DropboxOAuth2Flow.finish(request.query_params)
redirect_to('http://localhost:9088/')
