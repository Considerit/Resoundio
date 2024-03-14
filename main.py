import hyperdiv as hd
import os

from router import router

from dotenv import load_dotenv

load_dotenv()

########################
# load all files that define a route, otherwise it won't be added to the routes
from views.index import home
from views.songs import songs
from views.reaction import reaction
from views.reactions import reactions
from auth.auth_views import oauth_google_authorization
from auth.auth_views import auth_navigation_bar


def main():
    app = hd.template(
        title="Resound Reaction Concerts",
        logo="/assets/resound_logo.png",
        sidebar=False,
    )

    with app.app_title:
        hd.link(
            "@resoundio on YouTube",
            href="https://youtube.com/@resoundio",
            target="_blank",
        )

    with app.body:
        router.run()

    auth_navigation_bar(app)


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
