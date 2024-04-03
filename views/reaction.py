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

from views.shared import (
    is_small_screen,
    confirm_dialog,
    convert_seconds_to_time,
    convert_time_to_seconds,
)
from views.excerpt import (
    shortcuts_view,
    create_or_update_reaction_excerpt,
    keypoint_button,
)


def reaction(song_vid, song_key, reaction, video, base_width):
    reaction_vid = reaction["vid"]

    small_screen = is_small_screen()

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
        min_width="100%",
        max_width=f"{max(base_width + 200, window.width - 120)}px",
        border_radius=1,
        background_color="neutral-50",
        border_bottom="1px solid neutral-400",
        padding=(0, 0.25, 0.25, 0.25) if small_screen else (0, 2, 2, 2),
        margin=0 if small_screen else 1,
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
                reaction_video_yt = YoutubeEmbed(
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
                        shortcuts_view(keypoints, reaction_video_yt)

                        new_excerpt_button = hd.button(
                            f"Create new Reaction Excerpt at {convert_seconds_to_time(reaction_video_yt.current_time)}",
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

                    create_or_update_reaction_excerpt(
                        song_vid,
                        song_key,
                        reaction,
                        reaction_ui_state,
                        GetExcerptCandidates,
                        reaction_video_yt,
                        candidate=candidate,
                    )

            if len(excerpt_candidates) > 0:
                reaction_excerpt_table(
                    excerpt_candidates,
                    contributors,
                    reaction_ui_state,
                    song_vid,
                    song_key,
                    reaction,
                    reaction_video_yt,
                    GetExcerptCandidates,
                )


def reaction_excerpt_table(
    excerpt_candidates,
    contributors,
    reaction_ui_state,
    song_vid,
    song_key,
    reaction,
    reaction_video_yt,
    GetExcerptCandidates,
):
    with hd.table(margin_top=2):
        with hd.thead():
            with hd.tr():
                hd.td("Clip Time")
                hd.td("Song Anchor")
                # hd.td("Harvested by")
                hd.td("Notes")
                hd.td()
        with hd.tbody():
            for candidate in excerpt_candidates:
                with hd.scope(candidate):
                    contributor = contributors[candidate["user_id"]]
                    reaction_excerpt_item(
                        reaction_ui_state,
                        song_vid,
                        song_key,
                        reaction,
                        contributor,
                        candidate,
                        reaction_video_yt,
                        GetExcerptCandidates=GetExcerptCandidates,
                    )


def reaction_excerpt_item(
    reaction_ui_state,
    song_vid,
    song_key,
    reaction,
    contributor,
    candidate,
    reaction_video_yt,
    GetExcerptCandidates,
):
    small_screen = is_small_screen()

    clip_start = candidate["time_start"]
    clip_end = candidate.get("time_end", None)
    note = candidate.get("note", "_no notes given_")

    keypoint = float(clip_start)

    delete_state = hd.state(invoked=False)

    with hd.tr():
        with hd.td(max_width="200px"):
            with hd.hbox():
                keypoint_button(clip_start, reaction_video_yt, size="small")
                if clip_end:
                    hd.text("-")
                    keypoint_button(clip_end, reaction_video_yt, size="small")

        with hd.td():
            hd.text(convert_seconds_to_time(candidate["base_anchor"]))

        # with hd.td():
        #     with hd.hbox(gap=0.35):
        #         hd.avatar(image=contributor["avatar_url"], size="25px")
        #         hd.text(contributor["name"])

        # with hd.td(max_width="400px"):
        #     hd.markdown(note)

        with hd.td(max_width="400px"):
            with hd.vbox(gap=0.6, padding=(0.5, 0)):
                if note is not None and len(note) > 0:
                    hd.markdown(note, font_size="small")
                with hd.hbox(gap=0.3, align="center"):
                    hd.avatar(image=contributor["avatar_url"], size="25px")
                    hd.text(contributor["name"], font_size="small")

        with hd.td():
            if IsAdmin() or IsUser(contributor["user_id"]):
                if not reaction_ui_state.updating_excerpt:
                    with hd.box(
                        gap=1.5, direction="vertical" if small_screen else "horizontal"
                    ):
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
