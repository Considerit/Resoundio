import math, json

import hyperdiv as hd

from plugins.youtube_embed.youtube_embed import YoutubeEmbed
from plugins.multi_range_slider.multi_range_slider import MultiRangeSlider

from views.shared import (
    is_small_screen,
    convert_seconds_to_time,
    convert_time_to_seconds,
)

from database.aside_candidates import (
    get_aside_candidates,
    create_aside_candidate,
    update_aside_candidate,
    delete_aside_candidate,
)


def create_or_update_reaction_excerpt(
    song_vid,
    song_key,
    reaction,
    reaction_ui_state,
    GetExcerptCandidates,
    reaction_video_yt,
    candidate=None,
):
    reaction_id = reaction["vid"]
    keypoints = json.loads(reaction.get("keypoints", "[]"))

    state = hd.state(
        initialized=False,
        clip_start=0,
        clip_end=0,
        note=None,
        add_clip_end=None,
        edit_anchor=None,
        base_anchor=0,
        base_anchor_overridden=None,
        slider_key=0,
    )

    if not state.initialized:
        state.note = (candidate or {}).get("note", None)
        default_start = (
            reaction_video_yt.current_time
            if reaction_video_yt.current_time > 0
            else keypoints[0][0]
        )
        state.clip_start = (candidate or {}).get("time_start", default_start)
        state.clip_end = (candidate or {}).get("time_end", state.clip_start + 30)

        state.base_anchor = find_base_anchor(
            state.clip_start,
            keypoints,
        )
        state.add_clip_end = not not state.clip_end
        state.edit_anchor = False
        state.initialized = True

        state.slider_key += 1

    if state.add_clip_end and state.clip_end < state.clip_start:
        state.clip_end = state.clip_start + 30

    def close_form():
        if not candidate:
            reaction_ui_state.creating_excerpt = False
        else:
            reaction_ui_state.updating_excerpt = False

        form.reset()
        state.initialized = False

    excerpting = (
        reaction_ui_state.creating_excerpt or reaction_ui_state.updating_excerpt
    )
    with hd.form(
        width="100%",
        background_color="neutral-50" if not excerpting else "neutral-50",
        border=f"2px solid {'neutral-50' if not excerpting else 'primary-600'}",
        padding=(1, 2, 2, 2),
        border_radius="8px",
    ) as form:
        hd.h3(
            f"{'Create' if not candidate else 'Update'} Reaction Excerpt",
            font_size="large",
            font_weight="bold",
            text_align="center",
        )

        with hd.vbox(gap=2, align="center", justify="center"):
            with hd.box(width=f"{reaction_ui_state.video_width}px"):
                define_clip(
                    form,
                    state,
                    reaction_video_yt,
                    keypoints,
                )

            base_anchor_dialog_width = min(350, hd.window().width)

            with hd.vbox(
                gap=1,
                align="center",
                justify="center",
                width=f"{reaction_ui_state.video_width}px",
            ):
                anchor_clip(song_vid, song_key, state, form, base_anchor_dialog_width)

            notes_text = form.textarea(
                # "Notes (optional)",
                name="notes",
                placeholder="Why is this excerpt exceptional? [optional]",
                required=False,
                rows=2 + math.ceil(len(state.note or "") / 44),
                value=state.note if state.note is not None else "",
                width=f"{min(500, base_anchor_dialog_width-8)}px",  # f"{base_anchor_dialog_width}px",
            )
            if notes_text.changed:
                state.note = notes_text.value

            with hd.hbox(gap=0.1, align="center"):
                form.submit_button(
                    f"{'Create' if not candidate else 'Update'} Reaction Excerpt",
                    variant="primary",
                    size="large",
                    disabled=state.clip_end is not None
                    and state.clip_end < state.clip_start,
                )
                cancel = hd.button(
                    "cancel", variant="text", font_color="neutral-600", size="small"
                )

                if cancel.clicked:
                    close_form()

    if form.submitted:
        fd = form.form_data

        start = convert_time_to_seconds(fd["clip_start"])
        end = convert_time_to_seconds(fd["clip_end"])
        anchor = convert_time_to_seconds(fd["base_anchor"])

        if candidate:
            update_aside_candidate(
                candidate["id"],
                time_start=start,
                time_end=end,
                base_anchor=anchor,
                note=fd["notes"],
            )
        else:
            create_aside_candidate(
                song_key,
                reaction_id,
                time_start=start,
                time_end=end,
                base_anchor=anchor,
                note=fd["notes"],
            )
        GetExcerptCandidates.clear()
        close_form()


def define_clip(form, state, reaction_video_yt, keypoints):
    with hd.box(margin_bottom=1):
        shortcut_buttons = shortcuts_view(
            keypoints, reaction_video_yt, help_inline=True
        )

    current_range = state.clip_end - state.clip_start

    lower_bound = max(
        0,
        state.clip_start - current_range,
    )
    upper_bound = min(reaction_video_yt.duration, state.clip_end + current_range)
    slider = MultiRangeSlider(
        key=f"s{state.slider_key}",
        start=state.clip_start,
        end=state.clip_end,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        indicator=reaction_video_yt.current_time,
    )

    with hd.vbox(align="center", gap=1):
        with hd.hbox(gap=2, align="center", justify="center"):
            clip_start_text = form.text_input(
                value=convert_seconds_to_time(state.clip_start),
                pattern="[\d\.\:]",
                width=6,
                name="clip_start",
            )

            hd.text("–")

            clip_end_text = form.text_input(
                value=convert_seconds_to_time(state.clip_end),
                pattern="[\d\.\:]",
                width=6,
                name="clip_end",
            )

    # The rest of this function deals with keeping in sync the various ways clip
    # start and clip end can be manipulated.

    def update_slider_bounds():
        current_range = state.clip_end - state.clip_start

        lower_bound = max(
            0,
            state.clip_start - current_range,
        )
        upper_bound = min(
            reaction_video_yt.duration,
            state.clip_end + current_range,
        )

        slider.lower_bound = lower_bound
        slider.upper_bound = upper_bound

    def update_start_time(new_time_in_seconds):
        str_rep = convert_seconds_to_time(new_time_in_seconds)

        if slider.start != new_time_in_seconds:
            slider.start = new_time_in_seconds
        if clip_start_text.value != str_rep:
            clip_start_text.value = str_rep

        state.clip_start = new_time_in_seconds

        reaction_video_yt.current_time = new_time_in_seconds
        reaction_video_yt.playing = True

        if not state.base_anchor_overridden:
            state.base_anchor = find_base_anchor(
                state.clip_start,
                keypoints,
            )

    def update_end_time(new_time_in_seconds):
        str_rep = convert_seconds_to_time(new_time_in_seconds)

        if slider.end != new_time_in_seconds:
            slider.end = new_time_in_seconds
        if clip_end_text.value != str_rep:
            clip_end_text.value = str_rep

        state.clip_end = new_time_in_seconds

        reaction_video_yt.current_time = new_time_in_seconds - 2
        reaction_video_yt.playing = True

    def rebase_around_video_playhead():
        current_range = state.clip_end - state.clip_start
        update_start_time(reaction_video_yt.current_time)
        update_end_time(reaction_video_yt.current_time + current_range)
        reaction_video_yt.current_time = state.clip_start

        update_slider_bounds()

    for shortcut_button in shortcut_buttons:
        with hd.scope(shortcut_buttons):
            if shortcut_button.clicked:
                rebase_around_video_playhead()

    if reaction_video_yt.seeked:
        if not (state.clip_start <= reaction_video_yt.current_time <= state.clip_end):
            rebase_around_video_playhead()

    if slider.clicked_in_range:
        reaction_video_yt.current_time = float(slider.clicked_in_range)

    if clip_start_text.changed:
        try:
            update_start_time(convert_time_to_seconds(clip_start_text.value))
        except:
            hd.text(f"Bad value {clip_start_text.value}")

    if clip_end_text.changed:
        try:
            update_end_time(convert_time_to_seconds(clip_end_text.value))
        except:
            hd.text(f"Bad value {clip_end_text.value}")

    if slider.start != state.clip_start:
        update_start_time(slider.start)

    if slider.end != state.clip_end:
        update_end_time(slider.end)

    if state.clip_start > state.clip_end:
        update_end_time(state.clip_start + 30)

    if reaction_video_yt.current_time > state.clip_end:
        reaction_video_yt.current_time = state.clip_end - 2
    if reaction_video_yt.current_time < state.clip_start:
        reaction_video_yt.current_time = state.clip_start

    lower_bound_to_start = state.clip_start - slider.lower_bound
    end_to_upper_bound = slider.upper_bound - state.clip_end
    current_range = slider.upper_bound - slider.lower_bound

    # if the slider range is off center, readjust the slider bounds
    if (
        end_to_upper_bound < 0
        or lower_bound_to_start < 0
        or abs(lower_bound_to_start - end_to_upper_bound) / current_range > 0.2
    ):
        update_slider_bounds()

    return slider


def anchor_clip(song_vid, song_key, state, form, base_anchor_dialog_width):
    with hd.hbox(gap=0.5, align="center"):
        hd.markdown(f"Song anchor", font_weight="bold")

        with hd.tooltip(
            f"""To which part of _{song_key}_ does this Reaction Excerpt refer? This helps me know where
               to insert this excerpt into the song. Most of the time you don't need to set this because 
               the guess Resound provides is right about ~80% of the time."""
        ):
            hd.icon(
                "info-circle",
                font_size="medium",
                font_color="neutral-600",
            )

    with hd.vbox(gap=0.5, align="center"):
        base_video_yt = YoutubeEmbed(
            vid=song_vid,
            width=base_anchor_dialog_width,
            height=round(base_anchor_dialog_width * 0.5625),
            # controls=False,
            collect=False,
        )

        with hd.hbox(align="center", justify="center"):
            if base_video_yt.current_time != state.base_anchor:
                copy_from_playhead = hd.button(
                    convert_seconds_to_time(base_video_yt.current_time),
                    variant="text",
                    suffix_icon="arrow-right",
                    size="small",
                )

                if copy_from_playhead.clicked:
                    state.base_anchor = base_video_yt.current_time
                    state.base_anchor_overridden = True
            else:  # in hyperdiv, can't hide elements, so we'll create a placeholder
                hd.box(width="80px", height=1)

            base_anchor_text = form.text_input(
                value=convert_seconds_to_time(state.base_anchor),
                pattern="[\d\.\:]",
                width=6,
                name="base_anchor",
                disabled=not state.base_anchor_overridden,
            )

            edit_text = "reset" if state.base_anchor_overridden else "change"

            edit_button = hd.button(
                edit_text, variant="text", size="small", width="80px"
            )
            if edit_button.clicked:
                if not state.base_anchor_overridden:
                    state.base_anchor_overridden = True
                    reaction_video_yt.current_time = state.clip_start
                else:
                    state.base_anchor_overridden = False
                    state.base_anchor = find_base_anchor(
                        state.clip_start,
                        keypoints,
                    )

        base_video_yt.collect()

        if base_anchor_text.changed:
            state.base_anchor = convert_time_to_seconds(base_anchor_text.value)
            base_video_yt.current_time = state.base_anchor
            state.base_anchor_overridden = True

        if (
            not state.base_anchor_overridden
            and base_video_yt.current_time != state.base_anchor
        ):
            base_video_yt.current_time = state.base_anchor


def shortcuts_view(keypoints, reaction_video_yt, help_inline=False):
    shortcut_buttons = []

    with hd.hbox(gap=0.5, align="center", collect=False) as help_icon:
        with hd.tooltip(
            f"The Resound system tries to automatically detect when the song is actually playing in the reaction. As a consequence, we can link to key events in the reaction, such as when the song started, when the reactor paused the video, and when the reactor first reached the end of the song. These events are *not always right* and *not always complete*!"
        ):
            hd.icon("info-circle", font_size="small", font_color="#888")

    with hd.vbox(gap=0.5, align="center"):
        if not help_inline:
            with hd.hbox(align="center", gap=0.5):
                hd.text("Shortcuts")
                help_icon.collect()

        with hd.hbox(align="center", wrap="wrap"):
            for idx, keypoint in enumerate(keypoints):
                with hd.scope(keypoint):
                    notice = (
                        "song start"
                        if idx == 0
                        else "song end"
                        if idx == len(keypoints) - 1
                        else "pause"
                    )
                    bt = keypoint_button(
                        float(keypoint[0]),
                        reaction_video_yt=reaction_video_yt,
                        footer=notice,
                    )
                    shortcut_buttons.append(bt)
            if help_inline:
                help_icon.collect()

    return shortcut_buttons


def keypoint_button(keypoint, reaction_video_yt, footer=None, size="medium"):
    button = hd.button(variant="text", min_height="10px", size=size)
    with button:
        hd.text(
            convert_seconds_to_time(keypoint).split(".")[0],
            font_size="medium",
            padding=0,
            line_height="dense",
        )
        if footer:
            hd.text(
                f" {footer}",
                font_size="x-small",
                font_color="#999",
                line_height="dense",
            )

    if button.clicked:
        reaction_video_yt.current_time = keypoint

    return button


def find_base_anchor(clip_start, keypoints):
    last_base = 0
    for reaction_ts, base_ts in keypoints:
        if reaction_ts > clip_start:
            break
        last_base = base_ts

    print(f"{clip_start} has base match of {last_base}")
    return last_base
