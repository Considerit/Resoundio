import hyperdiv as hd
from router import router
import urllib.parse
import json
import math

from plugins.youtube_embed.youtube_embed import YoutubeEmbed
from auth.auth_model import IsAdmin, IsUser

from database.reactions import get_reaction
from database.videos import get_video
from database.aside_candidates import get_aside_candidates, create_aside_candidate, update_aside_candidate, delete_aside_candidate
from database.users import get_user, get_subset_of_users



@router.route("/songs/{vid_plus_song_key}/reaction/{vid_plus_reaction_channel}")
def reaction(vid_plus_song_key, vid_plus_reaction_channel): 
    song_vid = vid_plus_song_key[0:11]
    song_key = urllib.parse.unquote(vid_plus_song_key[12:])

    reaction_vid = vid_plus_reaction_channel[0:11]

    GetVideo = hd.task()
    GetVideo.run(get_video, reaction_vid)

    GetReaction = hd.task()
    GetReaction.run(get_reaction, reaction_vid)

    GetExcerptCandidates = hd.task()
    GetExcerptCandidates.run(get_aside_candidates, reaction_vid)



    if not GetVideo.result or not GetReaction.result or not GetExcerptCandidates.done:
        return

    video = GetVideo.result
    reaction = GetReaction.result
    excerpt_candidates = GetExcerptCandidates.result or []

    if len(excerpt_candidates) > 0:
        GetContributorAvatars = hd.task()
        GetContributorAvatars.run(get_subset_of_users, [candidate['user_id'] for candidate in excerpt_candidates])

        if not GetContributorAvatars.done:
            return

        contributors = { user['user_id']: user for user in GetContributorAvatars.result }

    keypoints = json.loads(reaction.get('keypoints', "[]"))
    keypoints.sort()

    reaction_ui_state = hd.state(
                            video_width=1000, 
                            creating_new_reaction_excerpt=False, 
                            editing_reaction_excerpt=False,
                            playhead_at_create = 0)

    video_width = reaction_ui_state.video_width


    # hd.h1(video['channel'], margin_bottom=.1)
    # hd.text(video['title'], font_size='small')

    with hd.hbox(gap=2):
        with hd.breadcrumb():
            with hd.breadcrumb_item(href='/'):
                hd.icon('house-door', margin_top=.3)

            hd.breadcrumb_item(
                song_key,
                href=f"/songs/{vid_plus_song_key}"
            )
            hd.breadcrumb_item(f"Reaction by {video['channel']}")

        with hd.hbox(gap=.5, align='center'):
            hd.text("video width", font_size='x-small', font_color="#888")

            video_width_input = hd.slider(min_value=150, max_value=2000, step=50, value=video_width)
            if video_width_input.changed:
                reaction_ui_state.video_width = int(video_width_input.value)


    with hd.hbox(gap=.5):
        y = YoutubeEmbed(vid=reaction_vid, width=video_width, height=round(video_width*0.5625))

    with hd.hbox(align='center'):
        hd.text("Events: ", font_size='small', font_color="#888")
        for idx, keypoint in enumerate(keypoints):
            with hd.scope(keypoint):
                notice = 'song start' if idx == 0 else 'song end' if idx == len(keypoints) - 1 else 'pause'
                keypoint_button(keypoint, embedded_video=y, footer=notice)


    with hd.vbox(gap=.35):
        with hd.hbox(align='center'):
            hd.text("Playhead:", font_size='small', font_color='#888', margin_right=.5)
            hd.text(f"{'{:03f}'.format(y.current_time)}")


            hd.text('seconds', margin_left=.2, margin_right=.6)

            if not reaction_ui_state.creating_new_reaction_excerpt:
                with hd.vbox(align='center', margin_top=1):
                    new_excerpt_button = hd.button('Create new Reaction Clip at playhead', variant="primary", prefix_icon='bookmark-star', font_size='medium')
                    hd.text("For when you find a reaction snippet to feature in a concert!", font_color="#888", font_size="x-small")

                if new_excerpt_button.clicked:
                    reaction_ui_state.creating_new_reaction_excerpt = True
                    reaction_ui_state.playhead_at_create = y.current_time

        if reaction_ui_state.creating_new_reaction_excerpt:
            reaction_excerpt_candidate(song_key, reaction['vid'], reaction_ui_state, GetExcerptCandidates)

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
                        contributor = contributors[candidate['user_id']]                
                        reaction_excerpt(contributor, candidate, embedded_video=y, GetExcerptCandidates=GetExcerptCandidates)



def keypoint_button(keypoint, embedded_video, footer=None):
    keypoint = float(keypoint)
    minutes = math.floor(keypoint / 60)
    seconds = round(60 * ((keypoint / 60) - math.floor(keypoint / 60)))

    keypoint_button = hd.button(variant="text", line_height='18px')
    with keypoint_button:
        hd.text(f"{minutes}:{'{:02d}'.format(seconds)}", font_size='medium', padding=0)
        if footer:
            hd.text(f" {footer}", font_size='x-small', font_color="#999")

    if keypoint_button.clicked:
        embedded_video.current_time = keypoint

def reaction_excerpt(contributor, candidate, embedded_video, GetExcerptCandidates):
    clip_start = candidate['time_start']
    clip_end = candidate.get('time_end', None)
    note = candidate.get('note', "_no notes given_")

    keypoint = float(clip_start)
    minutes = math.floor(keypoint / 60)
    seconds = round(60 * ((keypoint / 60) - math.floor(keypoint / 60)))

    with hd.tr():
        with hd.td():
            with hd.hbox():
                keypoint_button(clip_start, embedded_video)
                if clip_end:
                    hd.text('-')
                    keypoint_button(clip_end, embedded_video)

        with hd.td():
            with hd.hbox(gap=.35):
                hd.avatar(image=contributor['avatar_url'], size="25px")
                hd.text(contributor['name'])

        with hd.td():
            hd.markdown(note)

        with hd.td():
            if IsAdmin() or IsUser(contributor['user_id']):

                with hd.hbox(gap=2):
                    edit = hd.icon_button('pencil-square')
                    delete = hd.icon_button('trash')

                if delete.clicked: # TODO: need a confirm dialog here
                    delete_aside_candidate(candidate['id'])
                    GetExcerptCandidates.clear()




def reaction_excerpt_candidate(song_key, reaction_id, reaction_ui_state, GetExcerptCandidates, candidate_id=None):
    clip_start = reaction_ui_state.playhead_at_create

    def close_form():
        if not candidate_id:
            reaction_ui_state.creating_new_reaction_excerpt = False
        else: 
            reaction_ui_state.editing_reaction_excerpt = False    
                
    with hd.form(max_width=600, background_color="#eee", padding=1, border_radius="8px") as form:
        form.text_input("Approximate clip start (seconds)", name='clip_start', value=clip_start, required=True)
        form.text_input("Clip end (optional, in seconds)",  name='clip_end',placeholder="Does not have to be exact", required=False)
        form.textarea("Notes (optional)",  name='notes', placeholder="Why is this part of the reaction exceptional?", required=False)
        with hd.hbox(gap=.1):
            form.submit_button('Save', variant='primary')
            cancel = hd.button('cancel', variant='text', font_color='#888', font_size="small")

        if cancel.clicked:
            close_form()

    if form.submitted:
        fd = form.form_data
        create_aside_candidate(song_key, reaction_id, time_start=fd['clip_start'], time_end=fd['clip_end'], note=fd['notes'])
        GetExcerptCandidates.clear()
        close_form()
