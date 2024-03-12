import hyperdiv as hd
from router import router

from plugins.youtube_embed.youtube_embed import YoutubeEmbed
from views.songs import songs


@router.route("/")
def home():
    

    with hd.box(gap=2, padding=4, align="center"):

        # hd.link('songs', href="/songs")

        # hd.text("Hello this is it, Resound!")

        # y = YoutubeEmbed(vid="H0lvVOFt7-A")

        # hd.text(y.current_time)
        # seek_time = hd.text_input(placeholder="Time", input_type="number")
        # seek_button = hd.button("Seek")
        # if seek_button.clicked:
        #     y.current_time = float(seek_time.value)


        songs()
