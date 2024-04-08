import hyperdiv as hd
from router import router

from plugins.youtube_embed.youtube_embed import YoutubeEmbed
from plugins.script.script import Script
from plugins.iframe.iframe import IFrame

from views.songs import songs
from auth.auth_views import oauth_button

from views.shared import image_with_aspect_ratio


def view_app():
    loc = hd.location()

    nav_items = [
        {
            "label": "Help create a Reaction Concert",
            "href": "/help_with_concerts",
        },
        {"label": "Make a request", "href": "/requests"},
        {"label": "About us", "href": "/about"},
        # {"label": "Contact", "href": "/contact"},
        # {
        #     "label": "On YouTube",
        #     "href": "/youtube",
        # },
    ]

    with hd.hbox(
        justify="end",
        background_color="neutral-100",
        padding=(1, 0.5, 0.5, 0),
    ):
        oauth_button()

    with hd.vbox(align="center", gap=3, grow=1):
        with hd.box(align="center", background_color="neutral-100"):
            image_with_aspect_ratio(
                src="/assets/banner-transparent.webp",
                width="100%",
                max_width=1200,
                aspect_ratio=3961 / 675,
            )

            with hd.nav(
                max_width="900px",
                align="center",
                background_color="neutral-100",
                margin_top=2,
                direction="horizontal",
            ) as nav:
                for lnk in nav_items:
                    with hd.scope(lnk):
                        active = lnk["href"] == loc.path or (
                            lnk["href"].startswith("/help_with_concerts")
                            and loc.path.startswith("/help_with_concerts")
                        )
                        # hd.link(
                        #     lnk["label"],
                        #     href=lnk["href"],
                        #     font_color="primary-800"
                        #     if active
                        #     else "neutral-700",
                        #     font_size="medium",
                        #     padding=(1, 1, 1, 1),
                        #     border_bottom=f"2px solid {'primary' if active else 'neutral-100'}",
                        # )
                        hd.link(
                            lnk["label"],
                            href=lnk["href"],
                            font_color=(
                                "neutral-800"
                                if active
                                else "neutral-650" if active else "neutral-700"
                            ),
                            font_size="medium",
                            padding=(0.65, 1.25, 0.25, 1.25),
                            background_color="neutral-0" if active else "neutral-100",
                            border_radius=("6px", "6px", 0, 0) if active else 0,
                            # border_bottom=f"2px solid {'primary' if active else 'neutral-100'}",
                        )

        with hd.vbox(align="center"):
            # oauth_button(app)

            router.run()

    with hd.hbox(
        background_color="lime-50",
        min_height=5,
        align="center",
        justify="center",
        gap=0.5,
        margin_top=4,
        border_top="4px solid lime-500",
        padding=(0, 2, 0, 2),
    ):
        hd.markdown(
            """Developed by Travis Kriplean using **[Hyperdiv](https://hyperdiv.io/)**, a reactive web framework great for collecting reactions to reactions.""",
            font_size="small",
            font_color="lime-900",
        )


# @router.route("/")
# def home():
#     pass


@router.route("/requests")
def considerit_link():
    hd.markdown(
        """
        You can make a request for a reaction concert at <a href="https://resound.consider.it" target="_blank">resound.consider.it</a>. 
        You can also prioritize the concerts other people have suggested there. <a href="https://consider.it" target="_blank">Consider.it</a> is another opensource platform I've been working on 
        for many years :)
    """,
        max_width="700px",
    )


@router.route("/about")
def about():
    hd.markdown(
        """
        I'm <a href="https://traviskriplean.com" target="_blank">Travis Kriplean</a> and I create the Reactions Concerts 
        at <a href="https://www.youtube.com/channel/UCL7KNnyjribwiNTnSIosOeQ" target="_blank">@resoundio on YouTube</a>. 

        Broadly speaking, I'm an eclectic social 
        systems creator who loves improv-ing with kids, especially my sometimes-co-host son. 
        You can learn more at <a href="https://traviskriplean.com" target="_blank">my blog</a> or find me on 
        <a href="https://www.linkedin.com/in/travis-kriplean/">LinkedIn</a>. 

        Send me an email at 
        <a href="mailto:travis@consider.it">travis@consider.it</a> and I'll try to get back to you.

        If you'd like to support our work, please consider making a one-time or recurring donation at 
        <a href="https://buymeacoffee.com/resound" target="_blank">buymeacoffee.com/resound</a>.
    """,
        max_width="700px",
    )

    with hd.link(
        href="https://www.buymeacoffee.com/resound", target="_blank", margin_top="24px"
    ):
        hd.image(
            src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png",
            # alt="Buy Me A Coffee",
            height="60px",
            width="217px",
        )

    # Script(
    #     defn='<script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" data-name="bmc-button" data-slug="resound" data-color="#FFDD00" data-emoji="☕" data-font="Cookie" data-text="Buy me a coffee" data-outline-color="#000000" data-font-color="#000000" data-coffee-color="#ffffff" ></script>'
    # )


@router.route("/contact")
def contact():
    hd.markdown(
        """
        I'm <a href="https://traviskriplean.com" target="_blank">Travis Kriplean</a>. 
        You can find me on <a href="https://www.linkedin.com/in/travis-kriplean/">LinkedIn</a> or 
        <a href="https://traviskriplean.com" target="_blank">my blog</a>. Send me an email at 
        <a href="mailto:travis@consider.it">travis@consider.it</a> and I'll try to get back to you.
    """,
        max_width="700px",
    )


@router.route("/youtube")
def youtube():
    with hd.vbox(gap=1):
        hd.markdown(
            """
            Our Reaction Concert YouTube channel is <a href="https://www.youtube.com/channel/UCL7KNnyjribwiNTnSIosOeQ" target="_blank">@resoundio</a>. 
            
        """,
            max_width="700px",
        )

        IFrame(
            src="https://www.youtube.com/embed/videoseries?list=PLqAqdXtdNvrR9AHNOUaCzs7ejwwb4B6J9",
            width=560,
            height=315,
            frameborder=0,
        )
