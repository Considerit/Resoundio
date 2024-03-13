import hyperdiv as hd
from router import router
import urllib.parse
import json
import math

from plugins.youtube_embed.youtube_embed import YoutubeEmbed
from auth.auth_model import IsAdmin, IsUser

from database.reactions import get_reactions_by_song
from database.videos import get_videos
from database.aside_candidates import get_aside_candidates, get_aside_candidates_for_song, create_aside_candidate, update_aside_candidate, delete_aside_candidate
from database.users import get_user, get_subset_of_users


@router.route("/songs/{vid_plus_song_key}")
def reactions(vid_plus_song_key):
    vid = vid_plus_song_key[0:11]
    song_key = urllib.parse.unquote(vid_plus_song_key[12:])

    ReactionsForSong = hd.task()
    ReactionsForSong.run(get_reactions_by_song, song_key)


    if not ReactionsForSong.result:
        return

    reactions = ReactionsForSong.result

    VideosForReactions = hd.task() 
    VideosForReactions.run(get_videos, [reaction['vid'] for reaction in reactions]   )

    GetExcerptCandidates = hd.task()
    GetExcerptCandidates.run(get_aside_candidates_for_song, song_key)

    if not VideosForReactions.result or not GetExcerptCandidates.done: 
        return

    video_data = {video['vid']: video for video in VideosForReactions.result}

    excerpt_candidates_per_reaction = {}
    for candidate in GetExcerptCandidates.result or []:
        if candidate['reaction_id'] not in excerpt_candidates_per_reaction:
            excerpt_candidates_per_reaction[candidate['reaction_id']] = []
        excerpt_candidates_per_reaction[candidate['reaction_id']].append(candidate)


    with hd.breadcrumb():
        with hd.breadcrumb_item(href='/'):
            hd.icon('house-door', margin_top=.3)

        hd.breadcrumb_item(
            song_key,
            href=f"/songs/{vid_plus_song_key}"
        )

    with hd.h1():
        with hd.hbox(gap=.4, align='center'):
            artist, song = song_key.split(' - ')
            hd.text(f"{len(reactions)} Reactions", background_color='primary-300', padding=.5)
            hd.text(f"to")
            hd.markdown(f"_{song}_ by {artist}", background_color='warning-300', padding=.5)

    reactions_ui_state = hd.state(sort='views')

    def sort_reactions(r):
        if reactions_ui_state.sort == 'views':
            v = video_data[r['vid']]
            return -(v['views'] or 0)
        elif reactions_ui_state.sort == 'reaction clips identified':
            return -(len(excerpt_candidates_per_reaction.get(r['vid'], [])))

    reactions.sort(key=sort_reactions)

    with hd.hbox(gap=.5, align='center'):
        hd.text('sort by:', font_color='#888', font_size='small')

        for sort_method, ico in [('views', "sunglasses"), ('reaction clips identified', 'bookmark-star')]:
            with hd.scope(sort_method):
                if reactions_ui_state.sort == sort_method:
                    variant = 'primary'
                    outline = False
                    background_color = 'neutral-100'
                    color = '#000'
                else:
                    variant = 'neutral'
                    outline = False
                    background_color = 'neutral-50'
                    color = '#555'


                sort_button = hd.button(sort_method, variant=variant, outline=outline, line_height='24px', min_height='20px', background_color=background_color, font_color=color, border='none')
                if sort_button.clicked:
                    reactions_ui_state.sort = sort_method

    reaction_filter_el = hd.text_input(prefix_icon="filter", placeholder="filter reactions by channel", max_width=20)
    reaction_filter = reaction_filter_el.value

    with hd.list(style_type='none', padding_left=0):
        for reaction in reactions:
            with hd.scope(reaction):
                video = video_data[reaction['vid']]
                if not reaction_filter or reaction_filter.lower() in reaction['channel'].lower():
                    with hd.list_item(margin=0):
                        reaction_item(reaction, video)


def reaction_item(reaction, video):
    loc = hd.location()

    GetExcerptCandidates = hd.task()
    GetExcerptCandidates.run(get_aside_candidates, reaction['vid'])

    href = f"{loc.path}/reaction/{reaction['vid']}-{urllib.parse.quote(reaction['channel'])}"
    with hd.link(href=href, padding=.2, font_color='#000'):
        with hd.hbox(gap=1, background_color='#eee', border_radius='8px', padding=.5):
            hd.image(border_radius='8px', src=f"https://i.ytimg.com/vi/{video['vid']}/hqdefault.jpg", width=8)
            with hd.vbox(justify='center'):



                hd.h2(video['channel'])
                hd.text(video['title'], font_size='small')

                with hd.hbox(margin_top=1.5, gap=1):
                    if video.get('views', False):
                        hd.text(f"{video['views']} views", font_color='#888', font_size='small')

                    if GetExcerptCandidates.done:
                        excerpt_candidates = GetExcerptCandidates.result
                        if excerpt_candidates:
                            num_excerpts = len(excerpt_candidates)
                            excerpt_metric = f"{num_excerpts} reaction clips identified" if len(excerpt_candidates) != 1 else "1 reaction clip identified"
                            with hd.box(background_color='primary-500'):
                                hd.text( excerpt_metric, font_size='small', font_color='#fff', padding=(0, .5, 0, .5) )
                            



