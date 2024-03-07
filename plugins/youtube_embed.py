
import hyperdiv as hd


class YoutubeEmbed(hd.Plugin):
    vid = hd.Prop(hd.String, None)
    width = hd.Prop(hd.Int, 560)    
    height = hd.Prop(hd.Int, 315)
    current_time = hd.Prop(hd.Float, 0)

    # _assets = [('js-link', f"./assets/youtube_embed.js")]
    _assets = [('js-link', f"https://resoundio.com/assets/youtube_embed.js")]
