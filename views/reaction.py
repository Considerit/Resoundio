import hyperdiv as hd
from router import router
import urllib.parse
import json
import math

from plugins.youtube_embed.youtube_embed import YoutubeEmbed
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
    seconds = round(60 * ((seconds / 60) - math.floor(seconds / 60)))
    return f"{minutes}:{'{:02d}'.format(seconds)}"


def convert_time_to_seconds(ts):
    minutes, seconds = ts.split(":")
    return int(minutes) * 60 + int(seconds)


# @router.route("/songs/{vid_plus_song_key}/reaction/{vid_plus_reaction_channel}")
# def reaction(vid_plus_song_key, vid_plus_reaction_channel):
def reaction(song_vid, song_key, reaction, video, base_width):
    # song_vid = vid_plus_song_key[0:11]
    # song_key = urllib.parse.unquote(vid_plus_song_key[12:])

    # reaction_vid = vid_plus_reaction_channel[0:11]
    reaction_vid = reaction["vid"]
    # GetVideo = hd.task()
    # GetVideo.run(get_video, reaction_vid)

    # GetReaction = hd.task()
    # GetReaction.run(get_reaction, reaction_vid)

    GetExcerptCandidates = hd.task()
    GetExcerptCandidates.run(get_aside_candidates, reaction_vid)

    # if not GetVideo.result or not GetReaction.result or not GetExcerptCandidates.done:
    if not GetExcerptCandidates.done:
        return

    # video = GetVideo.result
    # reaction = GetReaction.result
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

    if "duration" in video:
        video_duration = convert_time_to_seconds(video["duration"])
    else:
        video_duration = keypoints[-1][0]

    reaction_ui_state = hd.state(
        video_width=min(base_width, 1000),
        creating_new_reaction_excerpt=False,
        editing_reaction_excerpt=False,
        playhead_at_create=0,
    )

    video_width = reaction_ui_state.video_width

    # hd.h1(video['channel'], margin_bottom=.1)
    # hd.text(video['title'], font_size='small')

    # with hd.hbox(gap=2):
    #     with hd.breadcrumb():
    #         with hd.breadcrumb_item(href="/"):
    #             hd.icon("house-door", margin_top=0.3)

    #         hd.breadcrumb_item(song_key, href=f"/songs/{vid_plus_song_key}")
    #         hd.breadcrumb_item(
    #             f"Reaction by {video['channel']}",
    #             href=f"/songs/{vid_plus_song_key}/reaction/{vid_plus_reaction_channel}",
    #         )

    loc = hd.location()
    window = hd.window()

    with hd.box(
        width=f"{min(base_width + 200, window.width - 20)}px",
        border_radius=1,
        background_color="neutral-50",
        padding=(0, 2, 2, 2),
        margin=1,
    ):
        with hd.hbox(justify="center"):
            # if video.get("views", False):
            #     hd.text(
            #         f"{video['views']} views",
            #         font_color="neutral-600",
            #         font_size="small",
            #     )

            with hd.link(href=loc.path, padding=(0.5, 1, 0.5, 1)):
                hd.icon("chevron-up", font_color="neutral-900", font_size="large")

        with hd.vbox(
            gap=1,
            justify="center",
            align="center",
        ):
            # with hd.vbox(justify="center", align="center"):
            with hd.h3():
                hd.link(
                    video["channel"],
                    href=loc.path,
                    font_size=1.75,
                    font_weight="bold",
                    font_color="neutral-900",
                    underline=True,
                )

                # hd.text(video["title"], font_size="small")

                # with hd.hbox(margin_top=0.5):
                #     if video.get("views", False):
                #         hd.text(
                #             f"{video['views']} views",
                #             font_color="neutral-600",
                #             font_size="small",
                #         )

            # with hd.hbox(gap=0.5, align="center", justify="center"):
            #     hd.text("video width", font_size="x-small", font_color="#888")

            #     video_width_input = hd.slider(
            #         min_value=min(base_width, 500),
            #         max_value=1500,
            #         step=50,
            #         value=video_width,
            #     )
            #     if video_width_input.changed:
            #         reaction_ui_state.video_width = int(video_width_input.value)

            with hd.hbox(gap=0.5):
                y = YoutubeEmbed(
                    vid=reaction_vid,
                    width=video_width,
                    height=round(video_width * 0.5625),
                )

            with hd.hbox(align="center", gap=0.5):
                hd.text("Events")
                with hd.hbox(gap=0.5, align="center"):
                    with hd.tooltip(
                        f"The Resound system tries to automatically detect when the song is actually playing in the reaction. As a consequence, we can link to key events in the reaction, such as when the song started, when the reactor paused the video, and when the reactor first reached the end of the song. These events are *not always right* and *not always complete*!"
                    ):
                        hd.icon("info-circle", font_size="small", font_color="#888")

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
                        keypoint_button(
                            float(keypoint[0]), embedded_video=y, footer=notice
                        )

            with hd.vbox(
                gap=0.35, grow=True, width="100%", max_width=f"{video_width}px"
            ):
                # with hd.hbox(align="center", justify="center"):
                #     hd.text(
                #         "Playhead:",
                #         font_size="small",
                #         font_color="#888",
                #         margin_right=0.5,
                #     )
                #     hd.text(f"{'{:03f}'.format(y.current_time)}")

                #     hd.text("seconds", margin_left=0.2, margin_right=0.6)

                if not reaction_ui_state.creating_new_reaction_excerpt:
                    with hd.vbox(align="center", margin_top=1, gap=0.5):
                        new_excerpt_button = hd.button(
                            f"Create new Reaction Excerpt at {convert_seconds_to_time(y.current_time)}",
                            variant="primary",
                            prefix_icon="bookmark-star",
                            font_size="medium",
                        )
                        with hd.tooltip(
                            "What makes for an \"excellent\" excerpt to feature? That's subjective. But I've found that the best snippets feature one of the following: (1) uniquely or humorously expresses what many people are feeling about an important part of the song; or (2) gives unique or professional insight into the artistry, lyrics, production, or underlying meaning of the song that most listeners wouldn't necessarily know and will deepen their appreciation.",
                            placement="bottom",
                        ):
                            hd.markdown(
                                "For when you find an <ins>excellent</ins> reaction excerpt to feature!",
                                font_color="#888",
                                font_size="x-small",
                            )

                    if new_excerpt_button.clicked:
                        reaction_ui_state.creating_new_reaction_excerpt = True
                        reaction_ui_state.playhead_at_create = y.current_time

                else:
                    reaction_excerpt_candidate(
                        song_key,
                        reaction,
                        video_duration,
                        reaction_ui_state,
                        GetExcerptCandidates,
                        embedded_video=y,
                    )

            if len(excerpt_candidates) > 0:
                with hd.table():
                    with hd.thead():
                        with hd.tr():
                            hd.td("Clip Time")
                            hd.td("Contributor")
                            hd.td("Notes")
                            hd.td()
                    with hd.tbody():
                        for candidate in excerpt_candidates:
                            with hd.scope(candidate):
                                contributor = contributors[candidate["user_id"]]
                                reaction_excerpt(
                                    song_key,
                                    reaction,
                                    contributor,
                                    candidate,
                                    video_duration,
                                    embedded_video=y,
                                    GetExcerptCandidates=GetExcerptCandidates,
                                )

            # with hd.vbox(gap=1, margin_top=6):
            #     hd.divider(spacing=0.5)
            #     # hd.h1("Find another reaction to identify Reaction Clips for")
            #     reactions(vid_plus_song_key)


def keypoint_button(keypoint, embedded_video, footer=None):
    button = hd.button(variant="text", min_height="10px")
    with button:
        hd.text(
            convert_seconds_to_time(keypoint),
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
        embedded_video.current_time = keypoint


def reaction_excerpt(
    song_key,
    reaction,
    contributor,
    candidate,
    video_duration,
    embedded_video,
    GetExcerptCandidates,
):
    clip_start = candidate["time_start"]
    clip_end = candidate.get("time_end", None)
    note = candidate.get("note", "_no notes given_")

    keypoint = float(clip_start)

    delete_state = hd.state(invoked=False)
    edit_state = hd.state(editing=False)

    with hd.tr():
        with hd.td(max_width="200px"):
            with hd.hbox():
                keypoint_button(clip_start, embedded_video)
                if clip_end:
                    hd.text("-")
                    keypoint_button(clip_end, embedded_video)

        with hd.td():
            with hd.hbox(gap=0.35):
                hd.avatar(image=contributor["avatar_url"], size="25px")
                hd.text(contributor["name"])

        with hd.td(max_width="400px"):
            hd.markdown(note)

        with hd.td():
            if IsAdmin() or IsUser(contributor["user_id"]):
                if edit_state.editing:
                    with hd.dialog() as dialog:
                        reaction_excerpt_candidate(
                            song_key,
                            reaction,
                            video_duration,
                            edit_state,
                            GetExcerptCandidates,
                            candidate=candidate,
                            embedded_video=embedded_video,
                        )
                    dialog.opened = True

                else:
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
                        edit_state.editing = True


def find_base_anchor(clip_start, keypoints):
    last_base = 0
    for reaction_ts, base_ts in keypoints:
        if reaction_ts > clip_start:
            break
        last_base = base_ts

    print(f"{clip_start} has base match of {last_base}")
    return last_base


def reaction_excerpt_candidate(
    song_key,
    reaction,
    video_duration,
    reaction_ui_state,
    GetExcerptCandidates,
    embedded_video,
    candidate=None,
):
    state = hd.state(
        initialized=False, clip_start=0, clip_end=0, note=None, add_clip_end=None
    )

    if not state.initialized:
        state.note = (candidate or {}).get("note", None)
        state.clip_start = (candidate or {}).get(
            "time_start", embedded_video.current_time
        )
        state.clip_end = (candidate or {}).get("time_end", None)
        state.add_clip_end = not not state.clip_end
        state.initialized = True

    reaction_id = reaction["vid"]

    def close_form():
        if not candidate:
            reaction_ui_state.creating_new_reaction_excerpt = False
        else:
            reaction_ui_state.editing = False

        form.reset()
        state.add_clip_end = False

    with hd.form(
        width="100%",
        background_color="neutral-100",
        padding=(1, 2, 2, 2),
        border_radius="8px",
    ) as form:
        with hd.vbox(align="center", justify="center"):
            hd.text("Identify an Excerpt", font_size="large", font_weight="bold")

            clip_interval_input(
                form=form,
                endpoint="start",
                interval_state=state,
                embedded_video=embedded_video,
                video_duration=video_duration,
                required=True,
            )

            if not state.add_clip_end:
                add_clip_end = hd.button("Add an Excerpt End")
                if add_clip_end.clicked:
                    state.clip_end = state.clip_start + 10
                    state.add_clip_end = True

            else:
                clip_interval_input(
                    form=form,
                    endpoint="end",
                    interval_state=state,
                    embedded_video=embedded_video,
                    video_duration=video_duration,
                )

                if state.clip_end < state.clip_start:
                    hd.text(
                        "Excerpt end must be greater than Excerpt start!",
                        font_color="warning-800",
                    )

        notes_text = form.textarea(
            "Notes (optional)",
            name="notes",
            placeholder="Why is this part of the reaction exceptional?",
            required=False,
            value=state.note if state.note is not None else "",
        )

        with hd.hbox(gap=0.1):
            form.submit_button(
                "Save",
                variant="primary",
                disabled=state.clip_end is not None
                and state.clip_end < state.clip_start,
            )
            cancel = hd.button(
                "cancel", variant="text", font_color="#888", font_size="small"
            )

        if cancel.clicked:
            close_form()

    if form.submitted:
        fd = form.form_data
        print(fd)
        base_anchor = find_base_anchor(
            float(fd["clip_start"]), json.loads(reaction.get("keypoints", "[]"))
        )
        if candidate:
            update_aside_candidate(
                candidate["id"],
                time_start=fd["clip_start"],
                time_end=fd["clip_end"],
                base_anchor=base_anchor,
                note=fd["notes"],
            )
        else:
            create_aside_candidate(
                song_key,
                reaction_id,
                time_start=fd["clip_start"],
                time_end=fd["clip_end"],
                base_anchor=base_anchor,
                note=fd["notes"],
            )
        GetExcerptCandidates.clear()
        close_form()


def clip_interval_input(
    form, endpoint, interval_state, embedded_video, video_duration, required=False
):
    current_val = getattr(interval_state, f"clip_{endpoint}")

    def update_time(new_val, interval_state):
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
                max_value=video_duration,
                grow=True,
                value=current_val,
            )

            with hd.vbox(gap=0.5):
                with hd.hbox(gap=0.5):
                    keypoint_button(
                        float(time_slider.value),
                        embedded_video,
                        footer=None,
                    )
                    copy_from_playhead = hd.button(
                        convert_seconds_to_time(embedded_video.current_time),
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
                        #     if embedded_video.current_time != current_val
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
                update_time(time_slider.value, interval_state)
            if time_text.changed:
                update_time(float(time_text.value), interval_state)
            if copy_from_playhead.clicked:
                update_time(embedded_video.current_time, interval_state)


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
