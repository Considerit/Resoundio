// Anon function required to avoid redefinition of `const hd = ` when we instantiating component twice.
(function() {

const hd = window.hyperdiv

/// Plugin constructor has 3 arguments: key (the html element id), the shadow DOM root, and initial props.
hd.registerPlugin('Script', function(key, shadow_root, initial_props) {


    // const script = document.createElement('script')

    const parser = new DOMParser()
    const doc = parser.parseFromString(initial_props.defn, 'text/html')
    const scriptFromString = doc.querySelector('script')

    const script = document.createElement('script')

    for (let attr of scriptFromString.attributes) {
      script.setAttribute(attr.name, attr.value);
    }


    shadow_root.appendChild(script)
    // document.body.appendChild(script)

    return function(prop_key, prop_value) {
        console.log('updated property key', prop_key)
        console.log('updated property value', prop_value)
    };
});

})();
