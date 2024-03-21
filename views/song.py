import hyperdiv as hd
from router import router
import urllib.parse

from plugins.youtube_embed.youtube_embed import YoutubeEmbed
from auth.auth_model import IsAdmin

from database.aside_candidates import (
    get_aside_candidates_for_song,
)

from database.songs import get_song

from auth.auth_views import auth_callout

from views.reactions import reactions_list


@router.route("/help_with_concerts/{vid_plus_song_key}")
def song_view(vid_plus_song_key):
    vid = vid_plus_song_key[0:11]
    song_key = urllib.parse.unquote(vid_plus_song_key[12:])

    SongData = hd.task()
    SongData.run(get_song, vid)

    if not SongData.result:
        return

    song = SongData.result

    GetExcerptCandidates = hd.task()
    GetExcerptCandidates.run(get_aside_candidates_for_song, song_key)

    if not GetExcerptCandidates.done:
        return

    excerpt_candidates_per_reaction = {}
    total_excerpt_candidates = 0
    for candidate in GetExcerptCandidates.result or []:
        if candidate["reaction_id"] not in excerpt_candidates_per_reaction:
            excerpt_candidates_per_reaction[candidate["reaction_id"]] = []
        excerpt_candidates_per_reaction[candidate["reaction_id"]].append(candidate)
        total_excerpt_candidates += 1

    auth_callout(justify="center")

    hd.anchor("start")

    window = hd.window()
    if window.width > 810:
        base_width = 750
    else:
        base_width = window.width - 60

    with hd.hbox(justify="center"):
        with hd.breadcrumb(
            margin_top=1,
        ):
            hd.breadcrumb_item(
                "All Upcoming Reaction Concerts", href="/help_with_concerts"
            )
            hd.breadcrumb_item(
                song_key,
                href=f"help_with_concerts/{vid}",
            )

    state = hd.state(editing_production_notes=False)
    production_notes = song.get("production_notes", None)

    with hd.vbox(
        gap=1,
        justify="center",
        max_width=f"{base_width}px",
        margin_top=1,
        align="center",
    ):
        hd.h1(
            song_key, font_size="3x-large"
        )  # , font_weight="bold", font_size="x-large")

        video_width = 560
        y = YoutubeEmbed(
            vid=vid,
            width=video_width,
            height=round(video_width * 0.5625),
        )

        with hd.vbox(gap=1.5):
            with hd.vbox(gap=1.5, align="center"):
                if not state.editing_production_notes:
                    with hd.hbox(gap=1):
                        hd.markdown(
                            production_notes or "_no production notes added_",
                            # font_size="small",
                            font_color="#000" if production_notes else "#888",
                        )
                        if IsAdmin():
                            edit_production = hd.icon_button("pencil-square")
                            if edit_production.clicked:
                                state.editing_production_notes = True

                else:
                    production_notes = hd.textarea(
                        placeholder="no production notes added",
                        value=production_notes or "",
                        size="small",
                        autofocus=True,
                    )

                    with hd.hbox(gap=0.2):
                        if hd.button("Save", variant="primary").clicked:
                            update_production_notes(song_key, production_notes.value)
                            state.editing_production_notes = False
                        if hd.button("cancel", variant="text").clicked:
                            state.editing_production_notes = False

            # num_excerpts = total_excerpt_candidates
            # excerpt_metric = (
            #     f"{num_excerpts} reaction excerpts identified"
            #     if num_excerpts != 1
            #     else "1 reaction clip identified"
            # )
            # hd.text(
            #     excerpt_metric,
            #     font_size="small",
            #     font_color="neutral-600",
            #     padding=(0, 0.5, 0, 0.5),
            # )

        # with hd.vbox(gap=1):

    reactions_list(song, base_width, excerpt_candidates_per_reaction)
