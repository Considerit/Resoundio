(function() {

const hd = window.hyperdiv
youtube_embed_state = {}

hd.registerPlugin('YoutubeEmbed', function(key, shadow_root, initial_props) {

    let player_el = document.createElement('div')

    let playing = initial_props.playing
    let width = initial_props.width
    let height = initial_props.height
    let time_update_intv = false
    let player = null
    let id = "player-" + initial_props.vid + "-" + key
    let duration_set = false
    let pause_after_buffered = false
    let buffering_state_observed = false
    let last_time_update = initial_props.current_time || 0

    // Using latest_external_current_time_set_at to approximately detect 
    // user seek events on the youtube video, as youtube doesn't 
    // provide a seek event for us to directly use.
    let latest_external_current_time_set_at = Date.now()

    player_el.id = id

    shadow_root.appendChild(player_el)

    console.log("Created YoutubeEmbed with id="+id+" and vid="+initial_props.vid)

    function setDuration() {
        if (!duration_set){
            try {
                duration = player.getDuration()
                hd.sendUpdate(key, 'duration', duration)
                duration_set = true
            } catch {
                console.error("Could not set duration:", initial_props.vid)
                setTimeout(function(){setDuration()}, 500)
            }
        }
    }

    function onPlayerReady(event) {

        if (initial_props.current_time) {
            player.seekTo( initial_props.current_time || 0 )
        }

        if (playing) {
            player.playVideo()
        }

        setDuration()
    }

    function onPlayerStateChange(event) {

        if (!time_update_intv)  // youtube iframe API doesn't provide an event for when 
                                      // user seeks, so we just keep the interval running
            time_update_intv = setInterval(updateCurrentTime, 100)

        if (!duration_set) 
            setDuration()

        if (event.data == YT.PlayerState.BUFFERING) {
            buffering_state_observed = true 
        }
        else if (event.data == YT.PlayerState.PLAYING ) {
            if (pause_after_buffered) {
                player.pauseVideo()
                pause_after_buffered = false
            } else if (!playing) {
                hd.sendUpdate(key, 'playing', true)
                playing = true 
            }
        } else {
            if (playing) {
                hd.sendUpdate(key, 'playing', false)
                playing = false
                updateCurrentTime()
            }

            // clearInterval(time_update_intv)
            // time_update_intv = false
        }
        
    }

    granularity = .25 // we don't want to update the time every millisecond. Granularity is how far we 
                     // allow the server's idea of the current time to drift, in seconds.
    function updateCurrentTime() {
        current_time = player.getCurrentTime()
        if (Math.abs(last_time_update - current_time) > granularity){
            hd.sendUpdate(key, 'current_time', current_time)

            ////////////////////////////////////////////////////////////////////
            // heuristic detection of whether this current_time update is due to 
            // the user seeking on the timeline
            ts = Date.now()
            time_since_external_current_time_update = (Date.now() - latest_external_current_time_set_at) / 1000
            difference_in_current_time_since_last_pulse = Math.abs(current_time - last_time_update)
            significant_difference = 3 // in seconds
            if (difference_in_current_time_since_last_pulse > significant_difference &&
                time_since_external_current_time_update > .5){
                hd.sendUpdate(key, 'seeked', true)
                latest_external_current_time_set_at = Date.now() 
                console.log("SEEKING TO", current_time)               
            } 

            ////////////


            last_time_update = current_time


        }
    }

    function onYouTubeIframeAPIReady() {
        player = new YT.Player(player_el, {
          height: height,
          width: width,
          videoId: initial_props.vid,
          playerVars: {
            'playsinline': 1,
            'controls': initial_props.controls ? 1 : 0,
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


    return function(prop_key, prop_value) {
        // console.log('updated property key', prop_key)
        // console.log('updated property value', prop_value)
        
        if (prop_key == 'currentTime') {
            new_time = parseFloat(prop_value)
            latest_external_current_time_set_at = Date.now()

            player.seekTo(new_time)
            if (playing) {
                player.playVideo()
            } else if (!buffering_state_observed){
                // We want the video to be loaded so we can see the current frame.
                // The only way to do it is to play it to get the data and then pause it.             
                pause_after_buffered = true       
                player.playVideo()
            }
        } else if (prop_key == 'playing') {
            playing = prop_value
            if (playing) {
                player.playVideo()
            } else {
                player.pauseVideo()
            }
        } else if (prop_key == 'width') {
            width = prop_value
            player.setSize(width, height)

        } else if (prop_key == 'height') {
            height = prop_value
            player.setSize(width, height)
        }

    };
});

})();
