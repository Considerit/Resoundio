import hyperdiv as hd
import os


class Script(hd.Plugin):
    defn = hd.Prop(hd.String, None)

    _assets = [
        (
            "js-link",
            os.path.join(os.path.dirname(__file__), "assets", "script.js"),
        )
    ]
