import hyperdiv as hd
import os


class MultiRangeSlider(hd.Plugin):
    # the selected range
    start = hd.Prop(hd.Float, 0)
    end = hd.Prop(hd.Float, 20)

    # the limits of acceptable range of values
    lower_bound = hd.Prop(hd.Float, 0)
    upper_bound = hd.Prop(hd.Float, 10)

    # a vertical line at a value
    indicator = hd.Prop(hd.Float, 0)

    # a string representing float value of value clicked on
    clicked_in_range = hd.Prop(hd.StringEvent, "")

    _assets = [
        (
            "js-link",
            "https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.1/nouislider.min.js",
        ),
        (
            "js-link",
            os.path.join(os.path.dirname(__file__), "assets", "multi_range_slider.js"),
        ),
        (
            "css-link",
            os.path.join(os.path.dirname(__file__), "assets", "multi_range_slider.css"),
        ),
    ]

    def reset(self):
        for prop in [
            "start",
            "end",
            "lower_bound",
            "upper_bound",
            "indicator",
        ]:
            self.reset_prop(prop)
