import hyperdiv as hd
import uuid
import os
from authlib.integrations.requests_client import OAuth2Session


class GoogleOAuth2(hd.Plugin):
    client_id = hd.Prop(hd.String)
    secret = hd.Prop(hd.String)

    redirectUri = hd.Prop(hd.String)
    scope = hd.Prop(hd.String, 'profile email openid')
    state = hd.Prop(hd.String, uuid.uuid4().hex)

    _assets = [("js-link", os.path.join(os.path.dirname(__file__), "assets", "google_oauth.js"))]





def google_oauth_authorization(redirect_uri, client_id, client_secret, login_via_oauth_handler, scope='profile email openid'):
    token_endpoint = 'https://oauth2.googleapis.com/token'
    api_endpoint = 'https://www.googleapis.com/oauth2/v1/userinfo'
    oauth_authorization(redirect_uri, token_endpoint, api_endpoint, client_id, client_secret, login_via_oauth_handler, scope='profile email openid')



def oauth_authorization(redirect_uri, token_endpoint, api_endpoint, client_id, client_secret, login_via_oauth_handler, scope):
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

        email = userinfo.get('email')
        name = userinfo.get('name')
        avatar = userinfo.get('picture')  # The URL to the user's profile pic
        avatar = avatar.replace("=s96-c", "=s512-c")

        login_via_oauth_handler(email, name, avatar)

        hd.local_storage.remove_item("oauth_state")

        loc.go(redirect_back_to.result)
