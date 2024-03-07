import hyperdiv as hd
from database.users import get_user, get_user_by_token, get_user_by_email, \
                           create_user

@hd.global_state
class CurrentUser(hd.task):
    def run(self):
        super().run(get_current_user)

    def fetch(self):
        self.run()
        return self.result

# todo: make this a task that gets set only when login_state.logged_in changes
def get_current_user():
    login_state = AuthState()
    if not login_state.logged_in:
        return None

    return get_user(login_state.current_user)



@hd.global_state
class AuthState(hd.BaseState):
    logged_in = hd.Prop(hd.Bool, False)
    show_login_dialog = hd.Prop(hd.Bool, False)
    current_user = hd.Prop(hd.String, None)
    checked_initial_session = hd.Prop(hd.Bool, False)


def log_user_in(user):
    login_state = AuthState()
    login_state.logged_in = True
    login_state.current_user = user['user_id']
    hd.local_storage.set_item("auth_token", user["token"])
    CurrentUser().clear()


def log_user_out():
    login_state = AuthState()
    login_state.logged_in = False
    login_state.current_user = None
    hd.local_storage.remove_item("auth_token")
    CurrentUser().clear()

def check_password(passwd, hashed_passwd, stored_salt):
    """
    Takes the user-input password, and the hashed password and salt
    stored in the DB and checks if the password in the DB matches the
    user-input password.
    """

    # Encode the password, hashed password, and the salt to bytes
    passwd_bytes = passwd.encode("utf-8")
    hashed_passwd_bytes = hashed_passwd.encode("utf-8")
    salt_bytes = stored_salt.encode("utf-8")

    # Compute a hashed version of the provided password using the stored salt
    computed_hash = bcrypt.hashpw(passwd_bytes, salt_bytes)

    # Check if the computed hash matches the stored hash
    return computed_hash == hashed_passwd_bytes


def check_login(email, password):
    user = get_user_by_email(email)
    if user and check_password(password, user["password"], user["salt"]):
        return user
    return None



def try_login_by_token(token = None):
    login_state = AuthState()

    # Look up the auth token in browser local storage.
    if token is None:
        token_request = hd.local_storage.get_item("auth_token")

        if not token_request.done:
            print('token request not done!')
            return 0
        else:
            token = token_request.result

    if token:
        user = get_user_by_token(token)
        print("DID I GET A USER", user, token)
        if user:
            # If a valid token is in local storage, we
            # automatically log the user in, without showing the
            # login form.
            log_user_in(user)
            return True

    login_state.checked_initial_session = True
    return None



def login_by_google_oauth(email, name, avatar):
    user = get_user_by_email(email)
    if not user:
        create_user(name, email, avatar_url=avatar)
        user = get_user_by_email(email)

    log_user_in(user)




