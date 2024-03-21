import hyperdiv as hd
import os

from router import router

from dotenv import load_dotenv

load_dotenv()

########################
# load all files that define a route, otherwise it won't be added to the routes
from views.index import view_app
from views.songs import songs
from views.reaction import reaction
from views.song import song_view
from auth.auth_views import oauth_google_authorization
from auth.auth_views import oauth_button
from auth.auth_model import login_if_token_available_on_page_load


def main():
    # app = hd.template(
    #     title="Resound Reaction Concerts",
    #     logo="/assets/resound_logo.png",
    #     sidebar=False,
    # )

    # with app.app_title:
    #     hd.link(
    #         "@resoundio on YouTube",
    #         href="https://youtube.com/@resoundio",
    #         target="_blank",
    #     )

    # with app.body:

    login_if_token_available_on_page_load()

    view_app()


index_page = hd.index_page(
    title="Resound",
    description="Contribute to Resound Reaction Concerts",
    keywords=("resound", "reaction", "reaction concert"),
    favicon="/assets/resound_logo.svg",
)


if __name__ == "__main__":
    from database.migrations import migrate_db

    migrate_db()

    hd.run(main, index_page=index_page)
