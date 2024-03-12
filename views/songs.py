import hyperdiv as hd
from router import router
from database.songs import AllSongs, update_production_notes

import urllib.parse

from plugins.youtube_embed.youtube_embed import YoutubeEmbed
from auth.auth_model import IsAdmin

# @router.route("/songs")
def songs():
    
    #with hd.box(gap=2, padding=4, align="center"):

    hd.h1("Upcoming Reaction Concerts")
    hd.text("""Help find meaningful excerpts from reaction videos to feature in these 
               upcoming Reaction Concerts! 
               (todo: put criteria for good excerpts to feature; link to resound.consider.it)""")


    with hd.list(style_type='none'):
        for song in (AllSongs().fetch() or []):
            with hd.scope(song):
                with hd.list_item(margin_bottom=2):
                    song_item(song)



def song_item(song):
    production_notes = song.get('production_notes', None)
    state = hd.state(editing_production_notes=False)
    href = f"/songs/{song['vid']}-{urllib.parse.quote(song['song_key'])}"

    if state.editing_production_notes:
        wrapper = hd.box()
    else:
        wrapper = hd.link(font_color='#000000', href=href)

    with wrapper:
        with hd.card(background_color='#eaeaea') as card:
            with hd.hbox(slot=card.image):
                y = YoutubeEmbed(vid=song['vid'])

            with hd.vbox(gap=0.5, align="center"):
                hd.text(song['song_key'], font_weight="bold", font_size='x-large')

                if not state.editing_production_notes:
                    with hd.hbox(gap=1):
                        hd.markdown( production_notes or '_no production notes added_', font_size="small", font_color='#000' if production_notes else '#888' )
                        if IsAdmin():
                            edit_production = hd.icon_button('pencil-square')
                            if edit_production.clicked:
                                state.editing_production_notes = True

                else:
                    production_notes = hd.textarea(placeholder="no production notes added", value=production_notes or '', size="small", autofocus=True)
                    
                    with hd.hbox(gap=.2):
                        if hd.button('Save', variant="primary").clicked:
                            update_production_notes(song['song_key'], production_notes.value)
                            state.editing_production_notes = False
                        if hd.button('cancel', variant="text").clicked:
                            state.editing_production_notes = False


                with hd.hbox(margin_top=1):
                    # hd.button("Help Find Reaction Excerpts",
                    #     variant="primary",
                    #     outline=False,
                    #     prefix_icon="music-note-list"
                    # )

                    # hd.icon_link("music-note-list", "Help Find Reaction Excerpts", href, font_color="neutral-0") #, classes="button button--primary button--medium button--standard button--has-label button--has-prefix")

                    with hd.link(
                        href=href,
                        direction="horizontal",
                        padding_top=.5,
                        padding_left=1,
                        padding_bottom=.5,
                        padding_right=1,
                        gap=0.5,
                        border="none",
                        hover_background_color="primary-500",
                        background_color="primary-600",
                        border_radius="medium",
                        width="fit-content",
                        align="center",
                        font_color="#fff",
                        font_size="small"
                    ):
                        hd.icon("music-note-list", padding_right=.25)
                        hd.text("Help Find Reaction Excerpts")



