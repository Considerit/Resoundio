import hyperdiv as hd
import datetime, json

from router import router
import urllib.parse

from plugins.youtube_embed.youtube_embed import YoutubeEmbed
from auth.auth_model import IsAdmin

from database.aside_candidates import asides_for_song


from database.users import get_subset_of_users
from database.songs import get_song, update_production_notes
from database.reactions import get_reactions_by_song

from auth.auth_views import auth_callout

from views.reactions import reactions_list

from views.shared import is_small_screen


@router.route("/help_with_concerts/{vid_plus_song_key}")
def song_view(vid_plus_song_key):
    vid = vid_plus_song_key[0:11]
    song_key = urllib.parse.unquote(vid_plus_song_key[12:])

    SongData = hd.task()
    SongData.run(get_song, vid)

    if not SongData.result:
        return

    song = SongData.result

    GetExcerptCandidates = asides_for_song(song_key, new_task=True)

    excerpt_candidates_per_reaction = {}
    total_excerpt_candidates = 0
    for candidate in GetExcerptCandidates.result or []:
        if candidate["reaction_id"] not in excerpt_candidates_per_reaction:
            excerpt_candidates_per_reaction[candidate["reaction_id"]] = []
        excerpt_candidates_per_reaction[candidate["reaction_id"]].append(candidate)
        total_excerpt_candidates += 1

    window_width = hd.window().width
    if window_width > 810:
        base_width = 750
    else:
        base_width = window_width - 60

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

    if window_width > 600:
        video_width = 560
    else:
        video_width = window_width - 40

    with hd.vbox(
        gap=1,
        justify="center",
        max_width=f"{base_width}px",
        margin_top=1,
        align="center",
        padding=(0, 0.5),
    ):
        with hd.vbox(align="center"):
            hd.h1(
                song_key, font_size="3x-large", text_align="center"
            )  # , font_weight="bold", font_size="x-large")

            if total_excerpt_candidates > 0:
                anchor_link_params = {
                    "font_color": "neutral-700",
                    "font_size": "small",
                    "underline": True,
                }
                with hd.hbox(align="center"):
                    hd.link("reactions", href="#reactions", **anchor_link_params)
                    hd.divider(vertical=True, spacing=1, height=0.75)
                    hd.link(
                        "excerpts found",
                        href="#candidate_excerpts",
                        **anchor_link_params,
                    )

        with hd.vbox(gap=1.5):
            with hd.vbox(gap=1.5, align="center"):
                if not state.editing_production_notes:
                    with hd.hbox(gap=1):
                        hd.markdown(
                            production_notes or "_no production notes added_",
                            # font_size="small",
                            font_color=(
                                "neutral-950" if production_notes else "neutral-600"
                            ),
                            max_width=f"{video_width}px",
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
                        width=f"{video_width}px",
                    )

                    with hd.hbox(gap=0.2):
                        if hd.button("Save", variant="primary").clicked:
                            update_production_notes(song_key, production_notes.value)
                            state.editing_production_notes = False
                            SongData.clear()
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

        y = YoutubeEmbed(
            vid=vid,
            width=video_width,
            height=round(video_width * 0.5625),
        )

    ReactionsForSong = hd.task()
    ReactionsForSong.run(get_reactions_by_song, song_key)

    if not ReactionsForSong.result:
        hd.spinner()
        return

    reactions = ReactionsForSong.result

    reactions_list(song, reactions, base_width, excerpt_candidates_per_reaction)

    if total_excerpt_candidates > 0:
        aside_candidate_list(
            song, reactions, base_width, (GetExcerptCandidates.result or []), y.duration
        )


def aside_candidate_list(song, reactions, base_width, all_candidates, song_duration):
    from views.reaction import convert_seconds_to_time

    num_candidates = len(all_candidates)
    candidate_metric = (
        f"{num_candidates} Candidate Reaction Excerpts"
        if num_candidates != 1
        else "1 Candidate Reaction Excerpt"
    )
    hd.anchor("candidate_excerpts")
    hd.h2(candidate_metric, text_align="center", font_size="large", margin_top=4)

    GetContributorAvatars = hd.task()
    GetContributorAvatars.run(
        get_subset_of_users,
        [candidate["user_id"] for candidate in all_candidates],
    )

    if not GetContributorAvatars.done:
        hd.spinner()
        return

    reactions_dict = {reaction["vid"]: reaction for reaction in reactions}

    contributors = {user["user_id"]: user for user in GetContributorAvatars.result}

    small_screen = is_small_screen()

    all_candidates.sort(key=lambda x: x["base_anchor"])

    with hd.table(margin_top=1):
        with hd.thead():
            with hd.tr():
                hd.td("Reaction")
                hd.td("Song Anchor")
                # hd.td("Reaction Clip")
                # hd.td("Harvested by")
                hd.td("Notes")

        with hd.tbody():
            for candidate in all_candidates:
                with hd.scope(candidate):
                    contributor = contributors.get(candidate["user_id"], None)

                    clip_start = candidate["time_start"]
                    clip_end = candidate.get("time_end", None)
                    note = candidate.get("note", "_no notes given_")

                    keypoint = float(clip_start)

                    with hd.tr(font_size="small" if small_screen else "medium"):
                        with hd.td():
                            with hd.vbox(gap=1):
                                with hd.hbox():
                                    hd.text(
                                        reactions_dict.get(
                                            candidate["reaction_id"], {}
                                        ).get("channel"),
                                        font_weight="bold",
                                    )
                                with hd.hbox():
                                    hd.text(
                                        convert_seconds_to_time(clip_start).split(".")[
                                            0
                                        ]
                                    )
                                    if clip_end:
                                        hd.text("-", margin=(0, 0.5, 0, 0.5))
                                        hd.text(
                                            convert_seconds_to_time(clip_end).split(
                                                "."
                                            )[0]
                                        )

                        with hd.td():
                            with hd.hbox(gap=0.35):
                                hd.text(
                                    convert_seconds_to_time(candidate["base_anchor"])
                                )

                        # with hd.td(max_width="200px"):
                        #     with hd.hbox():
                        #         hd.text(convert_seconds_to_time(clip_start))
                        #         if clip_end:
                        #             hd.text("-")
                        #             hd.text(convert_seconds_to_time(clip_end))

                        # with hd.td():
                        #     with hd.hbox(gap=0.35):
                        #         hd.avatar(image=contributor["avatar_url"], size="25px")
                        #         hd.text(contributor["name"])

                        with hd.td(max_width="400px"):
                            with hd.vbox(gap=0.6, padding=(0.5, 0)):
                                if note is not None and len(note) > 0:
                                    hd.markdown(note, font_size="small")
                                with hd.hbox(gap=0.3, align="center"):
                                    if contributor is None:
                                        hd.spinner()
                                    else:
                                        hd.avatar(
                                            image=contributor["avatar_url"], size="25px"
                                        )
                                        hd.text(contributor["name"], font_size="small")

    # export
    if IsAdmin():
        export_state = hd.state(show_export=False, created_after=None)

        with hd.box(margin_top=2, max_width=f"{min(hd.window().width-40, 800)}px"):
            if not export_state.show_export:
                export_candidates = hd.button("Export", variant="primary")

                if export_candidates.clicked:
                    export_state.show_export = True

            else:
                all_candidates.sort(key=lambda x: x["created_at"])

                with hd.dropdown() as dd:
                    trigger = hd.button("Created After", caret=True, slot=dd.trigger)
                    with hd.menu() as menu:
                        for c in all_candidates:
                            with hd.scope(c):
                                hd.menu_item(
                                    datetime.datetime.fromtimestamp(c["created_at"])
                                )

                    if trigger.clicked or menu.selected_item:
                        dd.opened = not dd.opened

                    if menu.selected_item:
                        export_state.created_after = menu.selected_item.label

                def get_pause(candidate):
                    if (
                        candidate["base_anchor"] == 0
                        or candidate["base_anchor"] >= song_duration - 5
                    ):
                        return 0
                    else:
                        return 3

                aside_export = {}
                overdub_export = {}

                for c in all_candidates:
                    channel = reactions_dict.get(c["reaction_id"], {}).get("channel")

                    if "overdub" in c["note"]:
                        if channel not in overdub_export:
                            overdub_export[channel] = []
                        overdub_export[channel].append(
                            c["time_start"] + (c["time_end"] - c["time_start"]) / 2
                        )

                    else:
                        if export_state.created_after and c["created_at"] < int(
                            datetime.datetime.strptime(
                                export_state.created_after, "%Y-%m-%d %H:%M:%S"
                            ).timestamp()
                        ):
                            continue

                        if channel not in aside_export:
                            aside_export[channel] = []

                        aside_export[channel].append(
                            [
                                c["time_start"],
                                c["time_end"],
                                c["base_anchor"],
                                get_pause(c),
                            ]
                        )

                exp = json.dumps(
                    {
                        "asides": aside_export,
                        "foregrounded_backchannel": overdub_export,
                    },
                    indent=2,
                )
                hd.textarea(
                    value=exp,
                    width=f"{min(hd.window().width-40, 800)}px",
                    rows=exp.count("\n") + 1,
                )
