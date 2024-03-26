import hyperdiv as hd
import os
from database.users import get_user, get_user_by_token, get_user_by_email, create_user


##########################
# AUTH STATE & ACCESSORS
####################


@hd.global_state
class AuthState(hd.BaseState):
    logged_in = hd.Prop(hd.Bool, False)
    show_login_dialog = hd.Prop(hd.Bool, False)
    current_user = hd.Prop(hd.String, None)
    checked_initial_session = hd.Prop(hd.Bool, False)


@hd.global_state
class CurrentUser(hd.task):
    def run(self):
        super().run(self.update)

    def fetch(self):
        self.run()
        return self.result

    def update(self):
        login_state = AuthState()
        if not login_state.logged_in:
            return None

        return get_user(login_state.current_user)


def IsAuthenticated():
    return not not CurrentUser().fetch()


def IsAdmin():
    current_user = CurrentUser().fetch()
    return current_user and current_user["email"] == os.getenv("ADMIN_EMAIL")


def IsUser(user_id):
    return CurrentUser().fetch() == user_id


###############################
# Login pathway helpers
#######################


def try_login_by_token(token):
    login_state = AuthState()

    user = get_user_by_token(token)
    if user:
        # log the user in if a valid token is in local storage
        log_user_in(user)

    return user


def login_by_google_oauth(userinfo):
    email = userinfo.get("email")

    user = get_user_by_email(email)
    if not user:
        name = userinfo.get("name")
        avatar = userinfo.get("picture")  # The URL to the user's profile pic
        avatar = avatar.replace("=s96-c", "=s512-c")

        create_user(name, email, avatar_url=avatar)
        user = get_user_by_email(email)

    log_user_in(user)


def login_if_token_available_on_page_load():
    login_state = AuthState()

    if not login_state.logged_in and not login_state.checked_initial_session:
        token_request = hd.local_storage.get_item("auth_token")
        if token_request.done:
            if token_request.result:
                try_login_by_token(token=token_request.result)
            login_state.checked_initial_session = True


################
# Log in and out
################


def log_user_in(user):
    login_state = AuthState()
    login_state.logged_in = True
    login_state.current_user = user["user_id"]
    hd.local_storage.set_item("auth_token", user["token"])
    CurrentUser().clear()


def log_user_out():
    login_state = AuthState()
    login_state.logged_in = False
    login_state.current_user = None
    hd.local_storage.remove_item("auth_token")
    CurrentUser().clear()


# def check_login(email, password):
#     user = get_user_by_email(email)
#     if user and check_password(password, user["password"], user["salt"]):
#         return user
#     return None


# def check_password(passwd, hashed_passwd, stored_salt):
#     """
#     Takes the user-input password, and the hashed password and salt
#     stored in the DB and checks if the password in the DB matches the
#     user-input password.
#     """

#     # Encode the password, hashed password, and the salt to bytes
#     passwd_bytes = passwd.encode("utf-8")
#     hashed_passwd_bytes = hashed_passwd.encode("utf-8")
#     salt_bytes = stored_salt.encode("utf-8")

#     # Compute a hashed version of the provided password using the stored salt
#     computed_hash = bcrypt.hashpw(passwd_bytes, salt_bytes)

#     # Check if the computed hash matches the stored hash
#     return computed_hash == hashed_passwd_bytes
