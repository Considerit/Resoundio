import hyperdiv as hd
from router import router
from database.songs import AllSongs, update_production_notes, update_song_status
from database.aside_candidates import asides_for_song
from database.reactions import get_reactions_by_song

import urllib.parse


from plugins.youtube_embed.youtube_embed import YoutubeEmbed
from auth.auth_model import IsAdmin, IsAuthenticated, CurrentUser

from auth.auth_views import auth_callout

from views.song import song_view

from enum import Enum


class SongStatus(Enum):
    backburner = -1
    in_process = 1
    unreleased = 2
    completed = 3


lists = [
    {
        "label": "In-process Reaction Concerts",
        "details": "Please help, these are concerts I'm actively working on.",
        "status": SongStatus.in_process,
    },
    {
        "label": "Unreleased Reaction Concerts",
        "details": "These are completed but have yet to be published.",
        "status": SongStatus.unreleased,
    },
    {
        "label": "Already Published",
        "details": "Thanks for the help!",
        "status": SongStatus.completed,
    },
    {
        "label": "On the Backburner",
        "details": "Status is up in the air, I may not return to them.",
        "status": SongStatus.backburner,
    },
]


# Thank you for helping identify excerpts of reaction videos to feature in the following
# upcoming Reaction Concerts. We're trying to commemorate songs that move us, using the active listening of
# reactors as the primary raw material. By helping us, you're transforming this into a communal undertaking.


@router.route("/help_with_concerts", redirect_from=("/",))
def songs():
    # with hd.box(gap=2, padding=4, align="center"):
    excerpt_tooltip = """What makes for a \"meaningful\" snippet to feature? That's subjective. But 
                I've found that the best snippets feature one of the following: (1) uniquely or 
                humorously expresses what many people are feeling about an important part of 
                the song; or (2) gives unique or professional insight into the artistry, 
                lyrics, production, or underlying meaning of the song that most listeners 
                wouldn't necessarily know and will deepen their appreciation."""

    logged_in = IsAuthenticated()

    loc = hd.location()
    query_args = dict(
        urllib.parse.parse_qsl(urllib.parse.urlsplit(loc.to_string()).query)
    )

    with hd.vbox(gap=3, align="center"):
        auth_callout(justify="center", primary=True)

        for lst in lists:
            label, details, status = lst.values()

            with hd.scope(label):
                with hd.box(gap=1, align="center"):
                    with hd.h1(margin_bottom=0):
                        hd.text(
                            label,
                            font_size="2x-large",
                            margin_bottom=0.15,
                        )

                    # if logged_in:
                    #     if False:
                    #         hd.markdown(
                    #             """ When you select
                    #         a reaction, you'll be provided a custom interface for skimming and/or
                    #         watching that reaction and marking interesting excerpts."""
                    #         )
                    #     else:
                    #         hd.markdown(
                    #             """To begin, select an Upcoming Reaction Concerts. You'll then
                    #         see the available reactions you can trowl through.""",
                    #             max_width="600px",
                    #             margin_bottom=2,
                    #         )

                    hd.text(
                        details,
                        font_size="medium",
                        margin_bottom=2,
                    )

                    with hd.list(style_type="none", padding=0):
                        for song in AllSongs().fetch() or []:
                            if (
                                SongStatus(song["status"]) is status
                                or song["status"] == None
                            ):
                                with hd.scope(song):
                                    with hd.list_item(margin_bottom=2):
                                        song_item(song)


def song_item(song):
    production_notes = song.get("production_notes", None)
    state = hd.state(editing_production_notes=False)
    href = f"/help_with_concerts/{song['vid']}-{urllib.parse.quote(song['song_key'])}"
    # href = f"help_with_concerts?selected_song={song['vid']}"

    GetExcerptCandidates = asides_for_song(song["song_key"], new_task=True)

    ReactionsForSong = hd.task()
    ReactionsForSong.run(get_reactions_by_song, song["song_key"])

    if not GetExcerptCandidates.done or not ReactionsForSong.done:
        return

    if state.editing_production_notes or not IsAuthenticated():
        wrapper = hd.box()
    else:
        wrapper = hd.link(font_color="neutral-950", href=href)

    # de6262 → #ffb88c
    window_width = hd.window().width
    if window_width > 600:
        video_width = 560
    else:
        video_width = window_width - 40

    my_status_label = ""

    for lst in lists:
        if lst["status"] is SongStatus(song["status"]):
            my_status_label = lst["label"]

    with hd.box():
        with wrapper:
            with hd.card(
                background_color="neutral-50", max_width=f"{video_width+40}px"
            ) as card:
                # with hd.hbox(
                #     gap=1,
                #     # background_color="neutral-50",
                #     background_gradient=(0, "neutral-200", "neutral-50"),
                #     border_radius="8px",
                #     padding=0.5,
                # ):
                with hd.box():
                    y = YoutubeEmbed(
                        vid=song["vid"],
                        width=video_width,
                        height=round(video_width * 0.5625),
                    )

                with hd.vbox():
                    with hd.vbox(gap=0.5, align="center"):
                        hd.text(
                            song["song_key"], font_weight="bold", font_size="x-large"
                        )

                        if not state.editing_production_notes:
                            with hd.hbox(gap=1):
                                hd.text(
                                    production_notes or "_no production notes added_",
                                    font_size="small",
                                    font_color=(
                                        "neutral-950"
                                        if production_notes
                                        else "neutral-600"
                                    ),
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
                                    update_production_notes(
                                        song["song_key"], production_notes.value
                                    )
                                    state.editing_production_notes = False
                                if hd.button("cancel", variant="text").clicked:
                                    state.editing_production_notes = False

                        with hd.hbox(margin_top=1):
                            # hd.button("Help Find Reaction Excerpts",
                            #     variant="primary",
                            #     outline=False,
                            #     prefix_icon="music-note-list"
                            # )

                            # hd.icon_link("music-note-list", "Help Find Reaction Excerpts", href, font_color="neutral-0") #, classes="button button--primary button--medium button--standard button--has-label button--has-prefix")

                            if IsAuthenticated():
                                with hd.link(
                                    href=href,
                                    direction="horizontal",
                                    padding_top=0.5,
                                    padding_left=1,
                                    padding_bottom=0.5,
                                    padding_right=1,
                                    gap=0.5,
                                    border="none",
                                    hover_background_color="fuchsia-500",
                                    background_gradient=(
                                        0,
                                        "fuchsia-700",
                                        "fuchsia-600",
                                    ),
                                    border_radius="medium",
                                    width="fit-content",
                                    align="center",
                                    font_color="#fff",
                                    font_size="small",
                                ):
                                    hd.icon("music-note-list", padding_right=0.25)
                                    hd.text("Help Find Reaction Excerpts")
                            else:
                                with hd.vbox(gap=0):
                                    with hd.box(justify="center"):
                                        auth_callout(
                                            justify="center",
                                            callout="Sign in to help find reaction excerpts:",
                                        )

                    with hd.hbox(gap=1, justify="center", margin_top=1):
                        reactions = ReactionsForSong.result
                        if reactions:
                            num_reactions = len(reactions)
                            reaction_metric = (
                                f"{num_reactions} reactions"
                                if num_reactions != 1
                                else "1 reaction"
                            )
                            hd.text(
                                reaction_metric,
                                font_size="small",
                                font_color="neutral-600",
                                padding=(0, 0.5, 0, 0.5),
                            )

                        excerpt_candidates = GetExcerptCandidates.result
                        if excerpt_candidates:
                            num_excerpts = len(excerpt_candidates)
                            excerpt_metric = (
                                f"{num_excerpts} excerpts"
                                if num_excerpts != 1
                                else "1 excerpt"
                            )
                            hd.text(
                                excerpt_metric,
                                font_size="small",
                                font_color="neutral-600",
                                padding=(0, 0.5, 0, 0.5),
                            )

        if IsAdmin():
            with hd.hbox(gap=1):
                with hd.dropdown() as dd:
                    trigger = hd.button(my_status_label, caret=True, slot=dd.trigger)
                    with hd.menu() as menu:
                        for lst in lists:
                            with hd.scope(lst):
                                hd.menu_item(lst["label"])

                    if trigger.clicked or menu.selected_item:
                        if menu.selected_item:
                            new_status = None
                            for lst in lists:
                                if lst["label"] == menu.selected_item.label:
                                    new_status = lst
                            if new_status["label"] != my_status_label:
                                update_song_status(
                                    song["song_key"], new_status["status"]
                                )
                                my_status_label = new_status["label"]

                        dd.opened = not dd.opened
