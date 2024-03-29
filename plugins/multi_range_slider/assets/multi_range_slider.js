(function() {

const hd = window.hyperdiv
youtube_embed_state = {}

/// Plugin constructor has 3 arguments: key (the html element id), the shadow DOM root, and initial props.
hd.registerPlugin('MultiRangeSlider', function(key, shadow_root, initial_props) {

    let wrapper = document.createElement('div')
    let slider_el = document.createElement('div')
    let indicator_el = document.createElement('div')

    let id = "multi-range-slider-"+key

    console.log(initial_props)

    let start = initial_props.start
    let end = initial_props.end
    let lower_bound = Math.round(initial_props.lowerBound)
    let upper_bound = Math.round(initial_props.upperBound)
    let duration = upper_bound - lower_bound

    let indicator = initial_props.indicator

    slider_el.id = id
    wrapper.style.height = (80 + 16).toString() + "px"
    // wrapper.style.marginTop = "20px"
    wrapper.style.position = 'relative'

    wrapper.appendChild(slider_el)
    wrapper.appendChild(indicator_el)

    shadow_root.appendChild(wrapper)


    let major = 30
    let minor = 15
    if (duration > 20 * 60) {
        major = 150
        minor = 60
    }
    if (duration > 40 * 60) {
        major = 300
        minor = 60
    }

    function filterPips(value, type) {
        if (value == 0) {
            return -1
        }
        if (value % major === 0){
            return 1
        }
        if (value % minor === 0){
            return 0
        }
        return -1
    }

    formatter = {
                to: function(val) { 
                    minutes = Math.floor(val/60).toString()
                    seconds =  Math.floor(val - minutes*60).toString()
                    tenths = Math.floor( 10 * (val - seconds - minutes*60) ) 
                    return minutes + ":" + seconds.padStart(2,'0') + "." + tenths  },
                from: function(val) { 
                    m,s = val.split(':')
                    return parseInt(m)*60 + parseFloat(sec)
                }
            }

    noUiSlider.create(slider_el, {
        start: [start, end],
        connect: true,
        step: .1,
        behaviour: 'tap-drag',
        range: {
            'min': lower_bound,
            'max': upper_bound
        },
        tooltips: formatter,
        pips: {
            mode: 'steps',
            density: 1,
            filter: filterPips,
            format: formatter
        }

    })

    indicator_el.style.position = 'absolute'
    indicator_el.style.zIndex = 99
    indicator_el.style.backgroundColor = '#034b6e'
    indicator_el.style.width = "2px"
    indicator_pos = 100 * (indicator - lower_bound) / (upper_bound - lower_bound)
    indicator_el.style.left = indicator_pos.toString() + "%"
    indicator_el.style.top = 0
    indicator_el.style.height = "56px" //slider_el.querySelector('.noUi-base').getBoundingClientRect().height.toString() + 'px'

    let slider = slider_el.noUiSlider

    function handleSliderChange(values, handle) {
        s = parseFloat(values[0])
        e = parseFloat(values[1])

        if (s != start) {
            start = s
            hd.sendUpdate(key, 'start', start)
        }
        if (e != end){
            end = e
            hd.sendUpdate(key, 'end', end)
        }
    }

    slider.on('change', handleSliderChange)


    let range_connector_el = slider_el.querySelector('.noUi-connect')

    function handleRangeClicked(evt){
        let rect = range_connector_el.getBoundingClientRect()
        let perc = (evt.clientX - rect.left) / rect.width
        let val = start + perc * (end - start)
        console.log("CLICKED IN RANGE", evt.clientX, perc, val, lower_bound, start, end)
        hd.sendUpdate(key, 'clicked_in_range', val.toString())
    }
    range_connector_el.addEventListener("click", handleRangeClicked)


    return function(prop_key, prop_value) {
        if (prop_key != "indicator"){
            console.log('updated property key', prop_key)
            console.log('updated property value', prop_value)
        }
        if (prop_key == 'start' && prop_value != start) {
            start = prop_value
            slider.set([start, end], false)
        } else if (prop_key == 'end' && prop_value != end) {
            end = prop_value
            slider.set([start, end], false)
        } else if (prop_key == 'lowerBound') {
            lower_bound = Math.round(prop_value)
            slider.updateOptions({
                range: {
                    'min': lower_bound,
                    'max': upper_bound
                }
            }
            )
            slider.set([start, end], false)


        } else if (prop_key == 'upperBound'){
            upper_bound = Math.round(prop_value)
            slider.updateOptions({
                range: {
                    'min': lower_bound,
                    'max': upper_bound
                }
            }
            )
            slider.set([start, end], false)

        } else if (prop_key == 'indicator'){
            indicator = prop_value
            indicator_pos = 100 * (indicator - lower_bound) / (upper_bound - lower_bound)
            indicator_el.style.left = indicator_pos.toString() + "%"
        }
    }

});


})();
