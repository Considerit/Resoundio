# requires authlib and requests

import hyperdiv as hd
import uuid
import os
from authlib.integrations.requests_client import OAuth2Session



###################################################################################################
# Button that will initiate oauth process and redirect to identity provider for authentication
#################################

class OAuth2(hd.Plugin):
    client_id = hd.Prop(hd.String)
    secret = hd.Prop(hd.String)

    redirectUri = hd.Prop(hd.String)
    scope = hd.Prop(hd.String, 'profile email openid')
    state = hd.Prop(hd.String, uuid.uuid4().hex)
    provider = hd.Prop(hd.String, 'google')

    _assets = [("js-link", os.path.join(os.path.dirname(__file__), "assets", "oauth2.js"))]



###########################################################################
# Handle the redirect back from the oauth provider containing the auth code.
# The redirect eeds to first be handled in the app, which should call one of the
# authorization methods below with little fuss.
################################################

def google_oauth2_authorization(redirect_uri, client_id, client_secret, oauth_callback, scope='profile email openid'):
    token_endpoint = 'https://oauth2.googleapis.com/token'
    api_endpoint = 'https://www.googleapis.com/oauth2/v1/userinfo'
    oauth2_authorization(redirect_uri, token_endpoint, api_endpoint, client_id, client_secret, oauth_callback, scope='profile email openid')



def oauth2_authorization(redirect_uri, token_endpoint, api_endpoint, client_id, client_secret, oauth_callback, scope):
    redirect_back_to = hd.local_storage.get_item("redirect_back_to")
    state = hd.local_storage.get_item("oauth_state")

    if state.done and redirect_back_to.done:

        loc = hd.location()
        authorization_response = f"{loc.protocol}//{loc.host}{loc.path}?{loc.query_args}"

        oauth = OAuth2Session(client_id, client_secret, 
                                scope=scope, 
                                state=state.result, 
                                redirect_uri=redirect_uri)

        # Exchange the authorization code for an access token
        token = oauth.fetch_token(  token_endpoint, 
                                    scope=scope,
                                    authorization_response=authorization_response, 
                                    client_id=client_id,
                                    client_secret=client_secret,
                                    auth=(client_id, client_secret))

        # Use the token to make requests to the API
        response = oauth.get(api_endpoint)
        userinfo = response.json()

        hd.local_storage.remove_item("oauth_state")

        oauth_callback(userinfo)

        loc.go(redirect_back_to.result)
