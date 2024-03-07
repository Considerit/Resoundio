// Anon function required to avoid redefinition of `const hd = ` when we instantiating component twice.
(function() {

const hd = window.hyperdiv


/// Plugin constructor has 3 arguments: key (the html element id), the shadow DOM root, and initial props.
hd.registerPlugin('YoutubeEmbed', function(key, shadow_root, initial_props) {

    player_el = document.createElement('div')

    id = player_el.id = "player-" + initial_props.vid
    shadow_root.appendChild(player_el)

    function onPlayerReady(event) {
        if (initial_props.current_time) {
            player.seekTo( initial_props.current_time || 0 )
        }
    }

    var time_update_intv = false
    function onPlayerStateChange(event) {
        if (event.data == YT.PlayerState.PLAYING ) {
            if (!time_update_intv)
                time_update_intv = setInterval(updateCurrentTime, 100)
        } else {
            clearInterval(time_update_intv)
            time_update_intv = false
        }
        
    }
    function updateCurrentTime() {
        hd.sendUpdate(key, 'current_time', player.getCurrentTime())
    }

    player = null
    function onYouTubeIframeAPIReady() {
        player = new YT.Player(player_el, {
          height: initial_props.height,
          width: initial_props.width,
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
            if (typeof YT !== 'undefined' && YT.Player) {
                clearInterval(api_ready_poll)
                onYouTubeIframeAPIReady()
            }
        }
        api_ready_poll = setInterval(checkYouTubeAPIReady, 10)

    } else {
        onYouTubeIframeAPIReady()
    }

    // last_current_seek_time = initial_props.current_time

    return function(prop_key, prop_value) {
        console.log('updated property key', prop_key)
        console.log('updated property value', prop_value)
        if (prop_key == 'currentTime') {
            new_time = parseFloat(prop_value)
            player.seekTo(new_time)
            player.pauseVideo()
            last_current_seek_time = new_time    
        }

    };
});

})();
