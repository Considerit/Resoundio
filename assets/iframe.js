// Anon function required to avoid redefinition of `const hd = ` when we instantiating component twice.
(function() {

const hd = window.hyperdiv;


/// Plugin constructor has 3 arguments: key (the html element id), the shadow DOM root, and initial props.
hd.registerPlugin('IFrame', function(key, shadow_root, initial_props) {

    const iframe = document.createElement('iframe');
    shadow_root.appendChild(iframe);

    iframe.src = initial_props.src
    iframe.height = initial_props.height
    iframe.width = initial_props.width 
    iframe.allow = initial_props.allow
    iframe.title = initial_props.title

    jsStatus.textContent = '(js) status = ' +  initial_props.xStatus;

    
    console.log('Init plugin component name = ', shadow_root.host.component.name);
    console.log('Init plugin component key = ', key);
    console.log('shadow_root', shadow_root);
    console.log('initial props: ', initial_props)


    // Update python compoenent property - property name not mangled.
    // hd.sendUpdate(key, 'x_status', '(from js) just loaded.')

    // newButton.addEventListener('click', () => {
    //     console_log('sending alert()');
    //     if (window.confirm(initial_props.xPrompt)) {
    //         console_log('You agreed.');
    //         hd.sendUpdate(key, 'x_agreed_with', true);
    //     } else {
    //         console_log('You agreed.');
    //         hd.sendUpdate(key, 'x_disagreed_with', true);
    //     }
    //     hd.sendUpdate(key, 'x_interacted_with', true);
    //   });
    

    // the constructor returns property update function.
    // **WARNING**: Prop key is mangled from snake_case into javaCase.
    return function(prop_key, prop_value) {
        console_log('updated property key', prop_key);
        console_log('updated property value', prop_value);
    };
});

})();
