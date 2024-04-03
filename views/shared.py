import hyperdiv as hd
import math


def is_small_screen():
    return hd.window().width < 900


def confirm_dialog(confirm_state, prompt="Are you sure you want to do that?"):
    with hd.dialog("Are You Sure?") as dialog:
        with hd.box(gap=1):
            hd.text(prompt)
            with hd.hbox(gap=1, justify="end"):
                if hd.button("Cancel").clicked:
                    dialog.opened = False
                    confirm_state.invoked = False
                delete_button = hd.button("Delete", variant="danger")
                if delete_button.clicked:
                    dialog.opened = False
                    confirm_state.invoked = False
    dialog.opened = True
    return delete_button


def convert_seconds_to_time(seconds):
    minutes = math.floor(seconds / 60)
    secs = math.floor(seconds - minutes * 60)
    tenths = math.floor((seconds - secs - minutes * 60) * 10)
    return f"{minutes}:{'{:02d}'.format(secs)}.{tenths}"


def convert_time_to_seconds(ts):
    minutes, seconds = ts.split(":")
    secs, tenths = seconds.split(".")

    return float(minutes) * 60 + float(secs) + float(tenths) / 10


class image_with_aspect_ratio(hd.image):
    _name = "image"

    aspect_ratio = hd.Prop(hd.CSSField("aspect-ratio", hd.Float))
