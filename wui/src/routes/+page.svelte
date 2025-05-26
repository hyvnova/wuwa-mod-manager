<script>
import Input from '$lib/input';
import { onMount } from 'svelte';


let messages = $state([]);


onMount(() => {
    if (window.eel === undefined) {
        console.error("Eel is not found, check out wui.py, something it's not configured correctly");
        return;
    }

    console.log("Eel is found, initializing...");

    const eel = window.eel;
    let input = new Input();


    function js_output_fn(message) {
        console.log("Received message from Python:", message);
        messages.push(message);
    }

    async function js_input_fn() {
        console.log("Requesting input from Python");
        return await input.read();
    }

    eel.expose(js_input_fn, "js_input_fn");
    eel.expose(js_output_fn, "js_output_fn");


    eel.call_handler('list');

});

</script>

<h1> BRRRRRRR patapin </h1>

{#each messages as message}
    <div class="message">
        <span class="message-text">{message}</span>
    </div>
{/each}