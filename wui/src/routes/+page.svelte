<script>
  import { onMount } from "svelte";

  let eel;
  let current_view = $state("list");
  let getting_input = $state(false);

  /**
   * Function to handle calls from Python
   * @type {function(string): void}
   */
  let call_handler;

  /**
   * @type {string[]}
   */
  let messages = $state([]);


   /**
   * @param {string} value
   */
   function is_spacing(value) {
    return /^\s*$/.test(value);
  }


  /**
   * Function to Switch the current view
   * @type {function(string): void}
   */
  function switch_view(view) {
    current_view = view;
    console.log("Current view set to:", current_view);
    call_handler(current_view);
  }

  let sidebarOpen = $state(true);
  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
  }

  onMount(() => {
    if (!window || !window.eel) {
      console.error(
        "Eel is not found, check out wui.py, something it's not configured correctly"
      );
      return;
    }

    console.log("Eel is found, initializing...");

    eel = window.eel;

    /**
     * @param {string} message
     */
    function js_output_fn(message) {
      console.log("Received message from Python:", message);

      if (is_spacing(message)) {
        // empty messages
        messages = [];
      } else {
        messages.push(message);
      }
    }

    /**
     * Called when python needs input from the user
     * @param {string} value
     */
    function js_request_input() {
      console.log("Python requested input, showing input dialog...");
      getting_input = true;
    }

    eel.expose(js_output_fn, "js_output_fn");
    eel.expose(js_request_input, "js_request_input");

    // Listeners de teclado, ahora correctamente dentro de onMount (solo en cliente)
    window.addEventListener("keydown", (event) => {
      if (event.key === "Tab" && !sidebarOpen) {
        event.preventDefault();
        toggleSidebar();
      }
      if (event.key === "Escape") {
        toggleSidebar();
      }
    });

    call_handler = (name) => {
      // Empty messages array
      messages = [];

      eel.call_handler(name.toLowerCase());

      // If quit, close the app
      if (name.toLowerCase() === "exit") {
        window.close();
      }

    };

    // Tells python IO functions are ready
    // eel.setup_io()

    switch_view("list");
  });

 

  let options = ["Exit", "List", "Install", "Delete", "Toggle", "Group", "Rebuild", "Download"];
</script>

<main
  class="grid grid-cols-[5%_1fr] gap-2 p-1 w-full"
  style="height: 100vh; overflow-y: auto; background: #181A1B;"
>
  <aside class="relative" style="min-width: 0;">
    <!-- Sidebar toggle button -->
    <button
      class="absolute top-4 left-2 z-20 bg-[#232526] text-gray-200 rounded-full p-2 shadow-lg hover:bg-[#282c34] transition-colors"
      aria-label="Toggle sidebar"
      onclick={toggleSidebar}
      style="outline: none;"
    >
      {#if sidebarOpen}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      {:else}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 6h16M4 12h16M4 18h7"
          />
        </svg>
      {/if}
    </button>

    <!-- Sidebar -->
    <section
      class="sidebar bg-gradient-to-b from-[#232526] to-[#414345] p-6 rounded-xl shadow-lg border-r border-gray-700 transition-all duration-300 ease-in-out flex flex-col"
      style="
              position: fixed;
              top: 0;
              left: 0;
              height: 100vh;
              width: {sidebarOpen ? '220px' : '56px'};
              min-width: 0;
              z-index: 10;
              overflow: hidden;
              padding-top: 3.5rem;
          "
      aria-expanded={sidebarOpen}
    >
      {#if sidebarOpen}
        <h2
          class="text-xl font-serif font-medium text-gray-100 tracking-wide text-center"
        >
          Menu
        </h2>
        <hr />
        <ul>
          {#each options as option, i}
            <li
              class="text-center font-serif block py-2 px-5 rounded-lg mb-2 text-gray-200 hover:bg-[#282c34] hover:text-white transition-colors font-light"
              class:mb-2={i < options.length - 1}
            >
              <button
                class="w-full h-full bg-transparent border-none text-inherit font-inherit"
                style="outline: none; cursor: pointer;"
                onclick={() => call_handler(option)}
              >
                {option}
              </button>
            </li>
          {/each}
        </ul>
      {:else}
        <div class=" flex flex-col items-center justify-center h-full">
          <span
            class="text-gray-400 text-sm rotate-[-90deg] whitespace-nowrap font-medium"
            >Menu</span
          >
        </div>
      {/if}
    </section>
  </aside>

  <!-- Main content area -->
  <section
    class="content bg-[#232526] p-8 rounded-xl shadow-xl flex flex-col overflow-auto"
    aria-label="Main content"
  >
    <h1 class="text-3xl font-serif font-bold mb-3 text-gray-100 tracking-tight">
      <span class="italic text-indigo-300">Hyvnt's</span> WuWa Mod Manager
    </h1>
    <p class="mb-6 text-gray-400 font-light">
      A stupid piece of software, done by stupid motherfucker <span
        class="italic text-indigo-200">Enjoy the suffering.</span
      >

      <span class="italic text-indigo-300">Sucker.</span>
    </p>

    <div
      class="overflow-y-auto flex-1 bg-gradient-to-br from-[#232526] to-[#2c2f34] p-6 rounded-lg shadow-md flex flex-col items-center border border-gray-700"
    >
      {#each messages as message}
          <div
            class="message typing-effect
        min-h-[30px]
        h-auto
        px-4 py-2
        bg-[#232526] text-gray-200
        font-mono text-lg
        shadow-sm
        border-x border-gray-700
        w-full text-center"
          >
            {message}
        </div>
      {/each}
    </div>

    {#if getting_input}
      <div class="flex justify-center items-center w-full mt-8">
      <input
        type="text"
        class="input animate-breathing border-2 border-indigo-500 focus:border-pink-500 ring-2 ring-indigo-400 focus:ring-pink-400 shadow-xl mt-0 w-full max-w-md bg-[#232526] text-indigo-200 font-mono text-xl font-bold rounded-md px-6 py-4 focus:outline-none transition-all duration-300"
        placeholder="Type your input here..."
        onkeydown={(e) => {
        if (e.key === "Enter") {
          eel.py_get_input(e.target.value);
          getting_input = false;
        }
        }}
        autofocus
      />
      </div>

    {/if}
  </section>
</main>

<svelte:head>
  <link
    href="https://fonts.googleapis.com/css2?family=DotGothic16&display=swap"
    rel="stylesheet"
  />
</svelte:head>

<style>
  .animate-breathing {
    animation: breathing 2.5s ease-in-out infinite;
  }
  @keyframes breathing {
    0% {
    border-color: #3e4041;
    }
    50% {
    border-color: #232526;
    }
    100% {
    border-color: #0f1214;
    }
  }
  </style>