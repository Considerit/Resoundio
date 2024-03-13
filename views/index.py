import hyperdiv as hd
from router import router

from plugins.youtube_embed.youtube_embed import YoutubeEmbed
from views.songs import songs


@router.route("/")
def home():
    with hd.box(gap=2, padding=4, align="center"):

        songs()
