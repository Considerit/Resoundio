import hyperdiv as hd
import os


class IFrame(hd.Plugin):
    src = hd.Prop(hd.String, None)
    width = hd.Prop(hd.Int, 560)
    height = hd.Prop(hd.Int, 315)
    title = hd.Prop(hd.String, None)
    frameborder = hd.Prop(hd.Int, 0)
    allow = hd.Prop(hd.String, None)

    _assets = [
        ("js-link", os.path.join(os.path.dirname(__file__), "assets", "iframe.js"))
    ]
