import hyperdiv as hd
from router import router
import urllib.parse
import json
import math

from plugins.youtube_embed.youtube_embed import YoutubeEmbed
from plugins.multi_range_slider.multi_range_slider import MultiRangeSlider

from auth.auth_model import IsAdmin, IsUser

from database.reactions import get_reaction
from database.videos import get_video
from database.aside_candidates import (
    get_aside_candidates,
    create_aside_candidate,
    update_aside_candidate,
    delete_aside_candidate,
)
from database.users import get_user, get_subset_of_users

# from views.reactions import reactions


def convert_seconds_to_time(seconds):
    minutes = math.floor(seconds / 60)
    secs = math.floor(seconds - minutes * 60)
    tenths = math.floor((seconds - secs - minutes * 60) * 10)
    return f"{minutes}:{'{:02d}'.format(secs)}.{tenths}"


def convert_time_to_seconds(ts):
    minutes, seconds = ts.split(":")
    secs, tenths = seconds.split(".")

    return float(minutes) * 60 + float(secs) + float(tenths) / 10


def reaction(song_vid, song_key, reaction, video, base_width):
    reaction_vid = reaction["vid"]

    GetExcerptCandidates = hd.task()
    GetExcerptCandidates.run(get_aside_candidates, reaction_vid)

    if not GetExcerptCandidates.done:
        return

    excerpt_candidates = GetExcerptCandidates.result or []

    if len(excerpt_candidates) > 0:
        GetContributorAvatars = hd.task()
        GetContributorAvatars.run(
            get_subset_of_users,
            [candidate["user_id"] for candidate in excerpt_candidates],
        )

        if not GetContributorAvatars.done:
            return

        contributors = {user["user_id"]: user for user in GetContributorAvatars.result}

    keypoints = json.loads(reaction.get("keypoints", "[]"))
    keypoints.sort()

    reaction_ui_state = hd.state(
        video_width=min(base_width, 1000),
        creating_excerpt=False,
        updating_excerpt=False,
    )

    video_width = reaction_ui_state.video_width

    loc = hd.location()
    window = hd.window()

    with hd.box(
        width=f"{max(base_width + 200, window.width - 120)}px",
        border_radius=1,
        background_color="neutral-50",
        border_bottom="1px solid neutral-400",
        padding=(0, 2, 2, 2),
        margin=1,
    ):
        with hd.hbox(justify="center"):
            with hd.link(href=loc.path, padding=(0.5, 1, 0.5, 1)):
                hd.icon("chevron-up", font_color="neutral-900", font_size="large")

        with hd.vbox(
            justify="center",
            align="center",
        ):
            with hd.h3():
                hd.link(
                    video["channel"],
                    href=loc.path,
                    font_size=1.75,
                    font_weight="bold",
                    font_color="neutral-900",
                    underline=True,
                    margin_bottom=1,
                )

            with hd.hbox(gap=0.5):
                y = YoutubeEmbed(
                    vid=reaction_vid,
                    width=video_width,
                    height=round(video_width * 0.5625),
                )

            with hd.vbox(grow=True, width="100%", max_width=f"{video_width+40}px"):
                if (
                    not reaction_ui_state.creating_excerpt
                    and not reaction_ui_state.updating_excerpt
                ):
                    with hd.vbox(align="center", margin_top=1, gap=0.4):
                        shortcuts_view(keypoints, reaction_video_yt=y)

                        new_excerpt_button = hd.button(
                            f"Create new Reaction Excerpt at {convert_seconds_to_time(y.current_time)}",
                            variant="primary",
                            prefix_icon="bookmark-star",
                            font_size="medium",
                            margin_top=1,
                        )
                        with hd.tooltip(
                            "What makes for an \"excellent\" excerpt to feature? That's subjective. But I've found that the best snippets feature one of the following: (1) uniquely or humorously expresses what many people are feeling about an important part of the song; or (2) gives unique or professional insight into the artistry, lyrics, production, or underlying meaning of the song that most listeners wouldn't necessarily know and will deepen their appreciation.",
                            placement="bottom",
                        ):
                            hd.markdown(
                                "For when you find an <ins>excellent</ins> reaction excerpt to feature!",
                                font_color="neutral-500",
                                font_size="x-small",
                            )

                        if new_excerpt_button.clicked:
                            reaction_ui_state.creating_excerpt = True

                else:
                    candidate = None
                    if reaction_ui_state.updating_excerpt:
                        for c in excerpt_candidates:
                            if c["id"] == reaction_ui_state.updating_excerpt:
                                candidate = c
                                break

                    reaction_excerpt_candidate(
                        song_vid,
                        song_key,
                        reaction,
                        reaction_ui_state,
                        GetExcerptCandidates,
                        reaction_video_yt=y,
                        candidate=candidate,
                    )

            if len(excerpt_candidates) > 0:
                with hd.table(margin_top=2):
                    with hd.thead():
                        with hd.tr():
                            hd.td("Clip Time")
                            hd.td("Song Anchor")
                            hd.td("Harvested by")
                            hd.td("Notes")
                            hd.td()
                    with hd.tbody():
                        for candidate in excerpt_candidates:
                            with hd.scope(candidate):
                                contributor = contributors[candidate["user_id"]]
                                reaction_excerpt(
                                    reaction_ui_state,
                                    song_vid,
                                    song_key,
                                    reaction,
                                    contributor,
                                    candidate,
                                    reaction_video_yt=y,
                                    GetExcerptCandidates=GetExcerptCandidates,
                                )

            # with hd.vbox(gap=1, margin_top=6):
            #     hd.divider(spacing=0.5)
            #     # hd.h1("Find another reaction to identify Reaction Clips for")
            #     reactions(vid_plus_song_key)


def keypoint_button(keypoint, reaction_video_yt, footer=None):
    button = hd.button(variant="text", min_height="10px")
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


def reaction_excerpt(
    reaction_ui_state,
    song_vid,
    song_key,
    reaction,
    contributor,
    candidate,
    reaction_video_yt,
    GetExcerptCandidates,
):
    clip_start = candidate["time_start"]
    clip_end = candidate.get("time_end", None)
    note = candidate.get("note", "_no notes given_")

    keypoint = float(clip_start)

    delete_state = hd.state(invoked=False)

    with hd.tr():
        with hd.td(max_width="200px"):
            with hd.hbox():
                keypoint_button(clip_start, reaction_video_yt)
                if clip_end:
                    hd.text("-")
                    keypoint_button(clip_end, reaction_video_yt)

        with hd.td():
            with hd.hbox(gap=0.35):
                hd.text(convert_seconds_to_time(candidate["base_anchor"]))

        with hd.td():
            with hd.hbox(gap=0.35):
                hd.avatar(image=contributor["avatar_url"], size="25px")
                hd.text(contributor["name"])

        with hd.td(max_width="400px"):
            hd.markdown(note)

        with hd.td():
            if IsAdmin() or IsUser(contributor["user_id"]):
                if not reaction_ui_state.updating_excerpt:
                    with hd.hbox(gap=2):
                        edit = hd.icon_button("pencil-square")
                        delete = hd.icon_button("trash")

                    if delete.clicked:
                        delete_state.invoked = True

                    if delete_state.invoked:
                        if confirm_dialog(
                            delete_state,
                            prompt="Are you sure you want to delete this clip?",
                        ).clicked:
                            delete_aside_candidate(candidate["id"])
                            GetExcerptCandidates.clear()

                    if edit.clicked:
                        reaction_ui_state.updating_excerpt = candidate["id"]


def find_base_anchor(clip_start, keypoints):
    last_base = 0
    for reaction_ts, base_ts in keypoints:
        if reaction_ts > clip_start:
            break
        last_base = base_ts

    print(f"{clip_start} has base match of {last_base}")
    return last_base


range_slider_width = 4 * 60


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


def create_clip(form, state, reaction_video_yt, keypoints, width):
    with hd.box(width=f"{width}px"):
        with hd.box(margin_bottom=1):
            shortcut_buttons = shortcuts_view(
                keypoints, reaction_video_yt, help_inline=True
            )

        lower_bound = max(0, state.clip_start - range_slider_width / 2)
        slider = MultiRangeSlider(
            start=state.clip_start,
            end=state.clip_end,
            lower_bound=lower_bound,
            upper_bound=min(
                reaction_video_yt.duration,
                lower_bound + range_slider_width,
            ),
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
            lower_bound = max(
                0, reaction_video_yt.current_time - range_slider_width / 2
            )
            upper_bound = min(
                reaction_video_yt.duration,
                lower_bound + range_slider_width,
            )

            slider.lower_bound = lower_bound
            slider.upper_bound = upper_bound

            current_range = state.clip_end - state.clip_start
            update_start_time(reaction_video_yt.current_time)
            update_end_time(reaction_video_yt.current_time + current_range)
            reaction_video_yt.current_time = state.clip_start

        for shortcut_button in shortcut_buttons:
            with hd.scope(shortcut_buttons):
                if shortcut_button.clicked:
                    rebase_around_video_playhead()

        if reaction_video_yt.seeked:
            if not (
                state.clip_start <= reaction_video_yt.current_time <= state.clip_end
            ):
                print("REBASING!", reaction_video_yt.current_time)
                rebase_around_video_playhead()

        if slider.clicked_in_range:
            reaction_video_yt.current_time = float(slider.clicked_in_range)

        if clip_start_text.changed:
            update_start_time(convert_time_to_seconds(clip_start_text.value))

        if clip_end_text.changed:
            update_end_time(convert_time_to_seconds(clip_end_text.value))

        # if playhead_to_start.clicked:
        #     update_start_time(reaction_video_yt.current_time)

        # if playhead_to_end.clicked:
        #     update_end_time(reaction_video_yt.current_time)

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


def reaction_excerpt_candidate(
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
    )

    if not state.initialized:
        state.note = (candidate or {}).get("note", None)
        state.clip_start = (candidate or {}).get("time_start", keypoints[0][0])
        state.clip_end = (candidate or {}).get("time_end", state.clip_start + 30)

        state.base_anchor = find_base_anchor(
            state.clip_start,
            keypoints,
        )
        state.add_clip_end = not not state.clip_end
        state.edit_anchor = False
        state.initialized = True

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
            create_clip(
                form,
                state,
                reaction_video_yt,
                keypoints,
                width=reaction_ui_state.video_width,
            )

            base_anchor_dialog_width = min(350, hd.window().width)
            anchor_width_px = f"{base_anchor_dialog_width}px"
            with hd.vbox(
                gap=1,
                align="center",
                justify="center",
                width=f"{reaction_ui_state.video_width}px",
            ):
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

                        edit_text = (
                            "reset" if state.base_anchor_overridden else "change"
                        )

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
                        state.base_anchor = convert_time_to_seconds(
                            base_anchor_text.value
                        )
                        base_video_yt.current_time = state.base_anchor
                        state.base_anchor_overridden = True

                    if (
                        not state.base_anchor_overridden
                        and base_video_yt.current_time != state.base_anchor
                    ):
                        base_video_yt.current_time = state.base_anchor

            with hd.vbox(gap=1, align="center"):
                notes_text = form.textarea(
                    # "Notes (optional)",
                    name="notes",
                    placeholder="Why is this excerpt exceptional? [optional]",
                    required=False,
                    rows=1 + math.ceil(len(state.note or "") / 44),
                    value=state.note if state.note is not None else "",
                    width=f"{min(500, hd.window().width)}px",  # f"{base_anchor_dialog_width}px",
                )
                if notes_text.changed:
                    state.note = notes_text.value

                # with hd.tooltip(
                #     "It's subjective. But I've found that the best snippets feature one of the following: (1) uniquely or humorously expresses what many people are feeling about an important part of the song; or (2) gives unique or professional insight into the artistry, lyrics, production, or underlying meaning of the song that most listeners wouldn't necessarily know and will deepen their appreciation.",
                #     placement="bottom",
                # ):
                #     hd.markdown(
                #         "What makes an <ins>excellent</ins> reaction excerpt to feature?",
                #         font_color="neutral-600",
                #         font_size="small",
                #     )

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


def clip_interval_input(
    form, endpoint, interval_state, reaction_video_yt, required=False
):
    current_val = getattr(interval_state, f"clip_{endpoint}")

    def update_time(new_val):
        if time_slider.value != new_val:
            time_slider.value = new_val
        if float(time_text.value) != new_val:
            time_text.value = new_val
        setattr(interval_state, f"clip_{endpoint}", new_val)

    with hd.vbox(gap=1, width="100%"):
        hd.text(f"Excerpt {endpoint}")
        with hd.hbox(gap=1):
            time_slider = hd.slider(
                min_value=0,
                max_value=reaction_video_yt.duration,
                grow=True,
                value=current_val,
            )

            with hd.vbox(gap=0.5):
                with hd.hbox(gap=0.5):
                    keypoint_button(
                        float(time_slider.value),
                        reaction_video_yt,
                        footer=None,
                    )
                    copy_from_playhead = hd.button(
                        convert_seconds_to_time(reaction_video_yt.current_time),
                        prefix_icon="arrow-left",
                        font_size="small",
                        line_height="dense",
                        min_height=0,
                        padding=0.25,
                        background_color="primary-50",
                        border="1px solid primary-600",
                        font_color="primary-950",
                        # base_style=hd.style(
                        #     opacity=1
                        #     if reaction_video_yt.current_time != current_val
                        #     else 0
                        # ),
                    )

                with hd.hbox(gap=0.5, align="center"):
                    time_text = form.text_input(
                        name=f"clip_{endpoint}",
                        required=required,
                        grow=True,
                        value=current_val,
                        max_width=6,
                    )

                    hd.text("secs")

            if time_slider.changed:
                update_time(time_slider.value)
            if time_text.changed:
                update_time(float(time_text.value))
            if copy_from_playhead.clicked:
                update_time(reaction_video_yt.current_time)

    current_val = getattr(interval_state, f"clip_{endpoint}")
    update_time(current_val)


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
