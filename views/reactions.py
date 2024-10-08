import hyperdiv as hd
from router import router
import urllib.parse

import json, math


from database.videos import get_videos

from views.reaction import reaction as reaction_view

from views.shared import is_small_screen, image_with_aspect_ratio


def reactions_list(song, reactions, base_width, excerpt_candidates):
    song_key = song["song_key"]
    song_vid = song["vid"]

    window = hd.window()

    reactions_ui_state = hd.state(sort="views", star_filter=False)

    VideosForReactions = hd.task()
    VideosForReactions.run(get_videos, [reaction["vid"] for reaction in reactions])

    if not VideosForReactions.result:
        with hd.box(font_size=4):
            hd.spinner(speed="5s", track_width=0.5)
        return

    video_data = {video["vid"]: video for video in VideosForReactions.result}

    small_screen = is_small_screen()

    sort_methods = [
        ("views", "sunglasses"),
        ("pauses", "pause-circle"),
        ("excerpts", "bookmark-star"),
    ]

    def sort_reactions(r):
        if reactions_ui_state.sort == "views":
            v = video_data[r["vid"]]
            return -(v["views"] or 0)
        elif reactions_ui_state.sort == "excerpts":
            return -(len(excerpt_candidates.get(r["vid"], [])))
        elif reactions_ui_state.sort == "pauses":
            keypoints = json.loads(r.get("keypoints", "[]"))
            return -len(keypoints)

    reactions.sort(key=sort_reactions)

    num_reactions = len(reactions)
    reaction_metric = (
        f"{num_reactions} Reactions" if num_reactions != 1 else "1 reaction"
    )

    star_filter = reactions_ui_state.star_filter

    loc = hd.location()
    query_args = urllib.parse.parse_qs(loc.query_args)

    #####################
    # handling pagination
    page_state = hd.state(current=1, mode=10)
    current_page = page_state.current
    page_mode = page_state.mode

    if page_mode == "show all":
        total_pages = 1
        reactions_on_page = reactions
    else:
        total_pages = math.ceil(num_reactions / page_mode)
        reactions_on_page = reactions[
            (current_page - 1) * page_mode : current_page * page_mode
        ]

    def pagination():
        if page_mode == "show all":
            return

        def pager_button(txt, is_current=False, visible=True):
            return hd.button(
                txt,
                variant="text",
                font_size="medium",
                font_color="neutral-600" if is_current else "blue-600",
                disabled=is_current or not visible,
                min_height=0.1,
                label_style=hd.style(padding=0.4),
            )

        with hd.hbox(gap=0, align="center", margin_top=1):
            prev_button = pager_button(
                "< previous",
                visible=current_page > 1,
            )
            if prev_button.clicked:
                page_state.current -= 1

            for page in range(total_pages):
                with hd.scope(page):
                    pager = pager_button(
                        f"{page + 1}", is_current=page + 1 == current_page
                    )

                    if pager.clicked and page_state.current != page + 1:
                        page_state.current = page + 1

            next_button = pager_button(
                "next >",
                visible=total_pages > current_page - 1,
            )
            if next_button.clicked:
                page_state.current += 1

        with hd.hbox(gap=0, align="center", margin_top=0):
            hd.text("Reactions per page:")
            for mode in [10, 25, 50, 100, "show all"]:
                with hd.scope(mode):
                    page_mode_btn = pager_button(
                        f"{mode}", is_current=mode == page_mode
                    )

                    if page_mode_btn.clicked:
                        page_state.mode = mode

    ######

    hd.anchor("reactions")
    hd.h2(reaction_metric, text_align="center", font_size="2x-large", margin_top=1.5)

    with hd.hbox(gap=0.5, align="center", margin_top=0.5):
        hd.text("sort by:", font_color="neutral-600", font_size="small", shrink=0)

        for sort_method, ico in sort_methods:
            with hd.scope(sort_method):
                if reactions_ui_state.sort == sort_method:
                    variant = "primary"
                    outline = False
                    background_color = "neutral-100"
                    color = "neutral-950"
                else:
                    variant = "neutral"
                    outline = False
                    background_color = "neutral-50"
                    color = "neutral-700"

                sort_button = hd.button(
                    sort_method,
                    variant=variant,
                    outline=outline,
                    line_height="24px",
                    min_height="20px",
                    background_color=background_color,
                    font_color=color,
                    border="none",
                )
                if sort_button.clicked:
                    reactions_ui_state.sort = sort_method

    with hd.hbox(
        gap=1,
        align="center",
        margin_top=0.5,
    ):
        if not small_screen:
            with hd.tooltip(
                "Filter to starred reactions. Helps you focus on the reactions you want to trowl through."
            ):
                if reactions_ui_state.star_filter:
                    star = hd.icon_button(
                        "star-fill",
                        font_size="large",
                        font_color="yellow-300",
                        grow=False,
                    )
                else:
                    star = hd.icon_button(
                        "star", font_size="large", font_color="neutral-300", grow=False
                    )

                if star.clicked:
                    reactions_ui_state.star_filter = not star_filter

        reaction_filter_el = hd.text_input(
            prefix_icon="search",
            placeholder="search reactions",
            width=f"{base_width - 35}px",
            grow=True,
            padding=0.2,
        )

        reaction_filter = reaction_filter_el.value

    reaction_selected = (
        None if "selected" not in query_args else query_args["selected"][0]
    )

    stars_local_storage = hd.local_storage.get_item("starred")

    if not stars_local_storage.done:
        stars = None
    elif not stars_local_storage.result:
        stars = {}
    else:
        stars = json.loads(stars_local_storage.result)

    with hd.box_list(
        # justify="center",
        align="center",
        min_height="100vh",
        gap=0.5,
        margin_top=0.5,
    ):
        for reaction in reactions_on_page:
            with hd.scope(reaction):
                video = video_data[reaction["vid"]]
                if (
                    not reaction_filter
                    or reaction_filter.lower() in reaction["channel"].lower()
                ) and (
                    not star_filter or not stars or stars.get(reaction["vid"], False)
                ):
                    is_selected = reaction_selected == reaction["vid"]

                    with hd.box_list_item(
                        margin=0,
                        padding=0,
                        min_width="100%",
                        max_width=f"{window.width}px"
                        if is_selected
                        else f"{base_width}px",
                    ):
                        excerpts = excerpt_candidates.get(video["vid"], [])

                        if is_selected:
                            reaction_view(
                                song_vid=song_vid,
                                song_key=song_key,
                                reaction=reaction,
                                video=video,
                                base_width=base_width,
                                excerpt_candidates=excerpts,
                            )

                        else:
                            with hd.hbox(gap=1, align="center"):
                                if not small_screen:
                                    with hd.tooltip(
                                        "Mark this reaction. Helps you track reactions you want to trowl through.",
                                        distance=16,
                                    ):
                                        if stars:
                                            starred = stars.get(reaction["vid"], False)
                                            if starred:
                                                star = hd.icon_button(
                                                    "star-fill",
                                                    font_size="large",
                                                    font_color="yellow-300",
                                                )
                                            else:
                                                star = hd.icon_button(
                                                    "star",
                                                    font_size="large",
                                                    font_color="neutral-300",
                                                )
                                        else:
                                            star = hd.icon_button(
                                                "star",
                                                font_size="large",
                                                font_color="neutral-300",
                                                disabled=True,
                                            )

                                    if star.clicked:
                                        stars[reaction["vid"]] = not starred
                                        hd.local_storage.set_item(
                                            "starred", json.dumps(stars)
                                        )

                                reaction_item(
                                    song_vid,
                                    channel=video.get("channel", ""),
                                    reaction_vid=video["vid"],
                                    keypoints=reaction.get("keypoints", "[]"),
                                    reaction_views=video.get("views", 0),
                                    reaction_title=video.get("title", ""),
                                    num_excerpts=len(excerpts),
                                    selected=is_selected,
                                )

    if page_mode != "show all":
        pagination()


@hd.cached
def reaction_item(
    song_vid,
    channel,
    reaction_vid,
    keypoints,
    reaction_views,
    reaction_title,
    num_excerpts,
    selected=False,
):
    # href = f"/songs/{vid_plus_song_key}/reaction/{reaction['vid']}-{urllib.parse.quote(reaction['channel'])}"

    loc = hd.location()
    query_args = urllib.parse.parse_qs(loc.query_args)
    query_args["selected"] = reaction_vid
    href = f"?{urllib.parse.urlencode(query_args)}"

    print(
        "SELECTED", loc.query_args, query_args, urllib.parse.urlencode(query_args), href
    )
    keypoints = json.loads(keypoints)

    small_screen = is_small_screen()

    channel_name = hd.markdown(
        f"<ins>{channel}</ins>", font_size="large", font_weight="bold", collect=False
    )

    excerpt_metric = f"{num_excerpts} excerpts" if num_excerpts != 1 else "1 excerpt"
    with hd.box(
        background_color="primary-500", collect=False
    ) as excerpt_candidates_count:
        hd.text(
            excerpt_metric,
            font_size="small",
            font_color="#fff",
            padding=(0, 0.5, 0, 0.5),
        )

    with hd.link(
        href=href,
        margin=0.2,
        font_color="neutral-700",
        grow=True,
        background_color="neutral-50",
        border_radius="8px",
        padding=0.5,
        shadow="small",
        border_bottom="1px solid neutral-400",
    ):
        if small_screen:
            with hd.box(margin_bottom=0.5):
                channel_name.collect()

        with hd.hbox(
            gap=1,
            align="center",
        ):
            image_with_aspect_ratio(
                border_radius="8px",
                src=f"https://i.ytimg.com/vi/{reaction_vid}/hqdefault.jpg",
                width=8,
                aspect_ratio=128 / 96,
            )

            with hd.vbox(justify="center", align="start", grow=1):
                if not small_screen:
                    channel_name.collect()

                if not small_screen:
                    hd.text(reaction_title, font_size="x-small")

                with hd.box(
                    margin_top=0 if small_screen else 1.5,
                    gap=0.25 if small_screen else 1,
                    direction="vertical" if small_screen else "horizontal",
                ):
                    hd.text(
                        f"{reaction_views} views",
                        font_color="neutral-600",
                        font_size="x-small",
                    )

                    hd.text(
                        f"{len(keypoints) - 2} {'pauses' if len(keypoints)-2 != 1 else 'pause'}",
                        font_color="neutral-600",
                        font_size="x-small",
                    )

                    if num_excerpts > 0:
                        excerpt_candidates_count.collect()

            with hd.link(href=href, padding=1):
                hd.icon("chevron-down", font_color="neutral-900", font_size="large")
