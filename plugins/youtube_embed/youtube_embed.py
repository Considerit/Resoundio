import hyperdiv as hd
import os


class YoutubeEmbed(hd.Plugin):
    vid = hd.Prop(hd.String, None)
    width = hd.Prop(hd.Int, 560)
    height = hd.Prop(hd.Int, 315)
    current_time = hd.Prop(hd.Float, 0)
    playing = hd.Prop(hd.Bool, False)
    duration = hd.Prop(hd.Float, 0)
    controls = hd.Prop(hd.Bool, True)

    seeked = hd.Prop(hd.BoolEvent, False)

    _assets = [
        (
            "js-link",
            os.path.join(os.path.dirname(__file__), "assets", "youtube_embed.js"),
        )
    ]
