import hyperdiv as hd
import os
from router import router

from auth.auth_model import CurrentUser, AuthState, \
                            try_login_by_token, log_user_out, \
                            login_if_token_available_on_page_load, \
                            login_by_google_oauth 

from plugins.oauth2.google_oauth import GoogleOAuth2



# Respond to oauth authorization request initiated by client js and redirected from Google
@router.route("/oauth/google")
def oauth_google_authorization():
    from plugins.oauth2.google_oauth import google_oauth_authorization
    client_id = os.getenv("GOOGLE_OAUTH2_CLIENT")
    client_secret = os.getenv("GOOGLE_OAUTH2_SECRET")

    google_oauth_authorization(redirect_uri='https://resoundio.com/oauth/google', 
                               login_via_oauth_handler=login_by_google_oauth,
                               client_id=client_id, 
                               client_secret=client_secret)



def auth_navigation_bar(template):
    current_user = CurrentUser().fetch()
    loc = hd.location()

    login_if_token_available_on_page_load()

    if not current_user:        
        with template.topbar_links:
            GoogleOAuth2( 
              client_id=os.getenv("GOOGLE_OAUTH2_CLIENT"),
              secret=os.getenv("GOOGLE_OAUTH2_SECRET"),
              redirectUri='https://resoundio.com/oauth/google', 
              scope='profile email openid')

    else:
        with template.topbar_links:
            hd.image(current_user['avatar_url'], width="25px", border_radius="50%")
            hd.text(f"{current_user['name']}", margin_left="12px")

            if hd.button("Log Out", size="small", variant="text").clicked:
                log_user_out()
                return










################################################
# Currently unused email/password authentication
# based on hyperdiv login demo app

# from auth.auth_model import check_login

# def login_dialog():
#     login_state = AuthState()
#     """The login screen."""

#     # Look up the auth token in browser local storage.
#     token_request = hd.local_storage.get_item("auth_token")
#     if not token_request.done:
#         return

#     token = token_request.result
#     if token:
#         try_login_by_token(token)


#     if login_state.logged_in:
#         return

#     # The login failure alert. This is `collec=False` because we
#     # need to access its state in code that is lexically before
#     # the spot where the alert is rendered.
#     failure_alert = hd.alert(
#         "Wrong user name or password",
#         variant="danger",
#         duration=3000,
#         collect=False,
#     )

#     # This task is used to asynchronously check the password on
#     # successful form submission.
#     check_login_task = hd.task()



#     def close_dialog():
#         login_state.show_login_dialog = False
#         failure_alert.opened = False

#     if login_state.logged_in:
#         close_dialog()
#         return

#     dialog = hd.dialog("Login", opened = True)

#     with dialog:
#         # The login form container.
#         with hd.box(align="center", justify="center", gap=1):
#             if check_login_task.running:
#                 # If the password checking task is running, just render a
#                 # loading spinner.
#                 hd.spinner()
#             else:
#                 # Otherwise render the login form.
#                 with hd.form(
#                     width=30,
#                     padding=2,
#                     #background_color="gray-50",
#                     border_radius="large",
#                 ) as form:                    
#                     user_name = form.text_input("User Name", required=True)
#                     email = form.text_input("Email", input_type="text", required=True)                        
#                     password = form.text_input(
#                         "Password", input_type="password", required=True
#                     )
#                     form.submit_button("Log In", variant="primary")

#                 if form.submitted:
#                     # This code runs when the user input the required
#                     # fields and submitted the form.

#                     # In case the failure alert is open from a
#                     # previous failed login, close it.
#                     failure_alert.opened = False
#                     # Launch the password checking task.
#                     check_login_task.rerun(
#                         check_login,
#                         email.value,
#                         password.value,
#                     )
#                 if hd.button('cancel').clicked:
#                     close_dialog()

#             # Render the failure alert.
#             failure_alert.collect()

#     # When the password checking task completes:
#     if check_login_task.finished:
#         user = check_login_task.result
#         if user:
#             # If password checking succeeded, log the user in.
#             log_user_in(user)
#             form.reset()
#             login_state.show_login_dialog = False
#         else:
#             # Otherwise show the failure alert.
#             failure_alert.opened = True

#     if not dialog.opened:
#         login_state.show_login_dialog = False




# def login_button(): 
#     login_state = AuthState()

#     if hd.button("Log In", size="small", variant="text").clicked:
#         login_state.show_login_dialog = True
