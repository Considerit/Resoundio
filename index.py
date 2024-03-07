import hyperdiv as hd
from plugins.youtube_embed.youtube_embed import YoutubeEmbed
from auth.auth_views import auth_navigation_bar
from router import router


@router.route("/")
def home():
    
    app = hd.template(title="Resound Reaction Concerts", logo="/assets/resound_logo.png")

    # theme = hd.theme()
    # theme.mode = 'dark'

    with app.body:
        with hd.box(gap=2, padding=4, align="center"):

            hd.text("Hello this is it, Resound!")

            y = YoutubeEmbed(vid="H0lvVOFt7-A")

            hd.text(y.current_time)
            seek_time = hd.text_input(placeholder="Time", input_type="number")
            seek_button = hd.button("Seek")
            if seek_button.clicked:
                y.current_time = float(seek_time.value)

    auth_navigation_bar(app)
