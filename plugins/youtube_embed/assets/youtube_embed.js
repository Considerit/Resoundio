// Anon function required to avoid redefinition of `const hd = ` when we instantiating component twice.
(function() {

const hd = window.hyperdiv
youtube_embed_state = {}

/// Plugin constructor has 3 arguments: key (the html element id), the shadow DOM root, and initial props.
hd.registerPlugin('YoutubeEmbed', function(key, shadow_root, initial_props) {


    if (!youtube_embed_state[initial_props.vid]){
        state = youtube_embed_state[initial_props.vid] = {
            key: key,
            playing: initial_props.playing,
            height: initial_props.height,
            width: initial_props.width,
            time_update_intv: false,
            player: null,
            player_el: document.createElement('div'),
            id: "player-" + initial_props.vid
        }
        state.player_el.id = state.id
    }

    state = youtube_embed_state[initial_props.vid]
    
    shadow_root.appendChild(state.player_el)

    console.log("Created YoutubeEmbed with id="+state.id+" and vid="+initial_props.vid)

    function onPlayerReady(event) {
        state = youtube_embed_state[initial_props.vid]
        if (initial_props.current_time) {
            state.player.seekTo( initial_props.current_time || 0 )
        }

        if (state.playing) {
            state.player.playVideo()
        }
    }

    function onPlayerStateChange(event) {
        state = youtube_embed_state[initial_props.vid]
        if (event.data == YT.PlayerState.PLAYING ) {

            if (!state.playing) {
                hd.sendUpdate(key, 'playing', true)
                state.playing = true 
            }
            if (!state.time_update_intv)
                state.time_update_intv = setInterval(updateCurrentTime, 100)
        } else {
            if (state.playing) {
                hd.sendUpdate(key, 'playing', false)
                state.playing = false
            }

            clearInterval(state.time_update_intv)
            state.time_update_intv = false
        }
        
    }
    function updateCurrentTime() {
        state = youtube_embed_state[initial_props.vid]
        hd.sendUpdate(state.key, 'current_time', state.player.getCurrentTime())
    }

    function onYouTubeIframeAPIReady() {
        state = youtube_embed_state[initial_props.vid]
        state.player = new YT.Player(state.player_el, {
          height: state.height,
          width: state.width,
          videoId: initial_props.vid,
          playerVars: {
            'playsinline': 1
          },
          events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange
          }
        })
    }
    if (typeof YT === 'undefined' || !YT.Player) {
        tag = document.createElement('script')
        tag.src = "https://www.youtube.com/iframe_api"
        firstScriptTag = document.getElementsByTagName('script')[0]
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag)

        function checkYouTubeAPIReady() {
            state = youtube_embed_state[initial_props.vid]

            if (typeof YT !== 'undefined' && YT.Player) {
                clearInterval(state.api_ready_poll)
                onYouTubeIframeAPIReady()
            }
        }
        state.api_ready_poll = setInterval(checkYouTubeAPIReady, 10)

    } else {
        onYouTubeIframeAPIReady()
    }


    return function(prop_key, prop_value) {
        state = youtube_embed_state[initial_props.vid]

        console.log('updated property key', prop_key)
        console.log('updated property value', prop_value)
        
        if (prop_key == 'currentTime') {
            new_time = parseFloat(prop_value)
            state.player.seekTo(new_time)
            if (state.playing) {
                state.player.playVideo()
            } else {
                state.player.pauseVideo()
            }
        } else if (prop_key == 'playing') {
            state.playing = prop_value
            if (state.playing) {
                state.player.playVideo()
            } else {
                state.player.pauseVideo()
            }
        } else if (prop_key == 'width') {
            state.width = prop_value
            state.player.setSize(state.width, state.height)

        } else if (prop_key == 'height') {
            state.height = prop_value
            state.player.setSize(state.width, state.height)
        }

    };
});

})();
