<script>
  import { onMount } from "svelte";
  import Fa from "svelte-fa";
  import { faList, faTimes, faTrash, } from "@fortawesome/free-solid-svg-icons";
  import { Splide, SplideSlide } from "@splidejs/svelte-splide";
  import "@splidejs/svelte-splide/css";
  import { writable } from "svelte/store";

  /**
   * @type {{
   *  name: string,
   *  path: string[],
   *  enabled: boolean
   * }[]}
   */
  let modlist = [
    {
      name: "CarlottaPants + Shirt NewFace",
      path: [
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\SavedMods\\CarlottaPants + Shirt NewFace",
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\Mods\\CarlottaPants + Shirt NewFace",
      ],
      enabled: false,
    },
    {
      name: "CovenCarlottaBody",
      path: [
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\SavedMods\\CovenCarlottaBody",
      ],
      enabled: false,
    },
    {
      name: "CovenCarlottaCrystalHair",
      path: [
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\SavedMods\\CovenCarlottaCrystalHair",
      ],
      enabled: false,
    },
    {
      name: "CovenCarlottaHair",
      path: [
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\SavedMods\\CovenCarlottaHair",
      ],
      enabled: false,
    },
    {
      name: "hair1",
      path: [
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\SavedMods\\hair1",
      ],
      enabled: false,
    },
    {
      name: "RabbitFX",
      path: [
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\SavedMods\\RabbitFX",
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\Mods\\RabbitFX",
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\SavedMods\\pb_pantsu2_2_2",
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\SavedMods\\HairCrystal",
      ],
      enabled: true,
    },
    {
      name: "SeraphimCantarella",
      path: [
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\SavedMods\\SeraphimCantarella",
      ],
      enabled: false,
    },
    {
      name: "Seraphim_UmbrellaMod",
      path: [
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\SavedMods\\Seraphim_UmbrellaMod",
      ],
      enabled: false,
    },
    {
      name: "skin",
      path: [
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\SavedMods\\skin",
      ],
      enabled: false,
    },
    {
      name: "Zani's button gave up!",
      path: [
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\SavedMods\\Zani's button gave up!",
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\Mods\\Zani's button gave up!",
      ],
      enabled: true,
    },
    {
      name: "hideui_uid_fog_v233",
      path: [
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\SavedMods\\hideui_uid_fog_v233",
        "C:\\Users\\Hyvnt\\AppData\\Roaming\\XXMI Launcher\\WWMI\\Mods\\hideui_uid_fog_v233",
      ],
      enabled: true,
    },
  ];

  const default_icon = "/default_icon.png";

  let mod_ui_resources = {
    "CarlottaPants + Shirt NewFace": [default_icon, default_icon, default_icon],
  };

  // If a mod has 2 or more different paths located at SavedMods, then it's considered a group
  function is_group(mod) {
    // Path whose before-last segment is "SavedMods"
    let memebers = mod.path.filter((p) => {
      const segments = p.split("\\");
      return segments[segments.length - 2] === "SavedMods";
    });
    return memebers.length > 1;
  }

  let selected = writable([]); // Store for selected mods
  let search_query = "";
  let enabled_filter = "all"; // Filter for enabled/disabled mods

  // This is where we apply filters to the modlist
  let matched_mods = modlist;

  let mobile = $state(false); // State for mobile view
  let show_panel = $state(true); // State for showing/hiding the panel
  let window_width = $state(0);
  onMount(() => {
    window_width = window.innerWidth;

    // If on mobile don't show the panel by default
    if (window.innerWidth < 768) {
      mobile = true;
      show_panel = false;
    }

    window.onresize = () => {
      window_width = window.innerWidth;
      if (window_width < 768) {
        mobile = true;
        show_panel = false; // Hide panel on mobile
      } else {
        mobile = false;
        show_panel = true; // Show panel on desktop
      }
    };
  });
</script>

<main class="flex flex-col p-1 w-full h-screen bg-[#181A1B]">
  <!-- Main content area -->
  <header
    class="content p-6 rounded-md flex flex-col mx-auto justify-center items-center"
    aria-label="Main header"
  >
    <h1 class="text-2xl font-serif font-bold mb-3 text-gray-100 tracking-tight">
      <span class="italic text-indigo-300">Hyvnt's</span> WuWa Mod Manager
    </h1>
    <p class="mb-6 text-gray-400 font-light">
      A stupid piece of software, done by stupid motherfucker <span
        class="italic text-indigo-200">Enjoy the suffering.</span
      >

      <span class="italic text-indigo-300">Sucker.</span>
    </p>
  </header>

  <!-- Main content -->
  <div class="flex flex-col mt-8 justify-center items-center">
    <!-- Filters -->
    <form class="flex flex-row justify-between items-center w-full max-w-xl">
      <!-- Search bar -->
      <input
        type="text"
        placeholder="Search mods..."
        class="p-3 rounded-md w-full
       bg-[#181A1B] text-gray-200 border border-gray-600
        focus:outline-none focus:ring-1 focus:ring-indigo-500
        "
        oninput={(e) => {
          search_query = e.target.value.toLowerCase();
          matched_mods = modlist.filter((mod) =>
            mod.name.toLowerCase().includes(search_query)
          );
        }}
      />

      <!-- Enabled filter -->
      <select
        class="ml-4 p-2 rounded border border-gray-600 bg-[#181A1B] text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        bind:value={enabled_filter}
        onchange={() => {
          if (enabled_filter === "all") {
            matched_mods = modlist;
          } else if (enabled_filter === "enabled") {
            matched_mods = modlist.filter((mod) => mod.enabled);
          } else if (enabled_filter === "disabled") {
            matched_mods = modlist.filter((mod) => !mod.enabled);
          }
        }}
        title="Filter by mod status"
        aria-label="Filter by mod status"
      >
        <option value="all" selected>All</option>
        <option value="enabled">Enabled</option>
        <option value="disabled">Disabled</option>
      </select>
    </form>

    <!--
    A grid of mod cards
  -->
    <div class="grid grid-cols-4 gap-4 self-center my-4 max-w-3xl">
      {#each matched_mods as mod}
        <div
          class="mod-card bg-[#08060c] border-[#3b4264]
          relative
          py-2 rounded-md shadow-md
          flex flex-col justify-center items-center border
          transition-all
          hover:scale-105
          hover:border-[#94aee6]
          {is_group(mod) ? ' col-span-2' : ''}"
        >
          <!-- Top Bar
            Contains mod name
          -->
          <div
            class="flex items-center justify-between mb-2 p-1 w-full"
            title={mod.name}
          >
            <h4
              class="bit_text flex-1 min-w-0 text-center text-lg
         overflow-hidden text-ellipsis whitespace-nowrap"
            >
              {mod.name}
            </h4>
          </div>

          <!-- Main content Image or Icon-->
          <div class="flex items-center justify-center h-full w-full">
            <Splide
              options={{
                type: "loop",
                perPage: 1,
                perMove: 1,
                pagination: false,
                pauseOnHover: true,
                arrows: false,
                autoplay: true,
                interval: 3000,
                speed: 500,
              }}
            >
              {#each mod_ui_resources[mod.name] || [default_icon] as resource, i}
                <SplideSlide>
                  <img
                    src={resource}
                    alt={mod.name + " icon " + (i + 1)}
                    class="w-32 h-32 object-contain rounded-md"
                  />
                </SplideSlide>
              {/each}
            </Splide>
          </div>

          <!-- Bottom Bar
              Contains utilities, like enable/disable, delete, etc.
              Currently only enable/disable 
            -->

          <!-- Enabled status -- an little overpositioned color in the bottom right corner-->
          <button
            class="absolute bottom-2 right-2 w-4 h-4 rounded-tl-full
            {mod.enabled ? 'bg-green-500' : 'bg-red-500'}
              transition-all duration-300
              hover:scale-200
              hover:border-2 hover:border-gray-300
            "
            title={mod.enabled ? "Enabled" : "Disabled"}
            aria-label={mod.enabled ? "Enabled" : "Disabled"}
            onclick={() => {
              mod.enabled = !mod.enabled;
            }}
          >
          </button>

          <!-- Select button -- a little overpositioned check input in top left-->
          <input
            type="checkbox"
            checked={$selected.includes(mod)}
            class="
              select-mod-checkbox
              opacity-0
              absolute top-2 left-2 w-6 h-6 rounded-br-full
              appearance-none border-2 border-gray-500
              checked:bg-indigo-500 checked:border-indigo-400
              bg-gray-700 hover:bg-gray-600 transition-all duration-300
              focus:outline-none focus:ring-2 focus:ring-indigo-500"
            title="Select mod"
            aria-label="Select mod"
            onclick={() => {
              if ($selected.includes(mod)) {
                selected.update((s) => s.filter((m) => m !== mod));
              } else {
                selected.update((s) => [...s, mod]);
              }
            }}
          />
        </div>
      {/each}
    </div>
  </div>

  <!-- Panel
    Panel it's overpositioned panel on the right side of the screen or center of the screen in mobile
    Will provide utilities for selected mods such as delete, enable/disable, grouping, etc.
    If will only be visible when at least one mod is selected
  -->
  {#if $selected.length > 0}

    <!-- If on mobile, show button to toggle panel -->
    {#if mobile && !show_panel}
      <button
        class="fixed bottom-4 right-4 bg-indigo-600 text-white p-3 rounded-full
        shadow-lg hover:bg-indigo-700 transition-colors duration-200 z-50"
        onclick={() => {
          show_panel = !show_panel;
        }}
        title="Toggle Mod Panel"
        aria-label="Toggle Mod Panel"
      >
        <Fa icon={faList} />
      </button>
    {/if}

    {#if show_panel}
    <div
      class="fixed top-8 right-6 w-xl bg-[#221f23]/60 p-4
      border border-gray-700 shadow-2xl z-50 rounded-xl backdrop-blur-md"
      style="transition: transform 0.3s ease-in-out; height: 94vh;"
      id="mod-panel"
    >
      <button
        class="absolute top-2 right-2 text-gray-400 hover:text-gray-200"
        onclick={() => {
          selected.set([]);
          show_panel = false;
        }}
        title="Clear selection"
        aria-label="Clear selection"
      >
        <Fa icon={faTimes} />
      </button>

      <!-- Main buttons -->
      <div class="flex flex-col space-y-2 my-8">
        <!-- Delete button -->
        <button
          class="bit_text bg-red-600 text-white p-2 rounded-md
          hover:bg-red-700 transition-colors duration-200 inline-flex items-center justify-evenly"
          onclick={() => {
            $selected.forEach((mod) => {
              modlist = modlist.filter((m) => m !== mod);
            });
            selected.set([]);
          }}
          title="Delete selected mods"
          aria-label="Delete selected mods"
        >
          <Fa icon={faTrash} />
          Delete Selected Mods
        </button>
      </div>

      <!-- List selected mods-->
      <div class="mb-4">
        <h4 class="text-md font-semibold text-gray-200 mb-2 text-center">
          Selected Mods
        </h4>
        <ul class="list-decimal list-inside text-gray-300">
          {#each $selected as mod}
            <li class="bit_text text-sm">{mod.name}</li>
          {/each}
        </ul>
      </div>
    </div>
    {/if}
  {/if}
</main>

<svelte:head>
  <link
    href="https://fonts.googleapis.com/css2?family=DotGothic16&display=swap"
    rel="stylesheet"
  />
</svelte:head>

<style>
  .bit_text {
    font-family: "DotGothic16", sans-serif;
  }

  /*
   When mod car it's hovered, make selection checkbox visible
   */
  .mod-card:hover .select-mod-checkbox {
    opacity: 1;
    transition: opacity 0.3s ease-in-out;
  }

  /* If select-mod-checkbox is checked, make it visible */
  .select-mod-checkbox:checked {
    opacity: 1;
  }
</style>
