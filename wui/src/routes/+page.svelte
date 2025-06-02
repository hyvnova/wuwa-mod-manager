<script lang="ts">
  /**
   * WuWa Mod‑Manager UI (Svelte 5)
   * -------------------------------------------------------------
   * ‣ Cleaned‑up & commented.
   * ‣ Uses Tailwind CSS for styling.
   * ‣ Strongly‑typed via JSDoc / TS for better DX.
   * ‣ All state lives in Svelte stores → less manual DOM poking.
   * -------------------------------------------------------------
   * @typedef {Object} Mod
   * @property {string}   name     – Display name.
   * @property {boolean}  enabled  – Current on/off state.
   * @property {string[]} path     – List of full paths that compose the mod.
   */

  /* ───────────────────────────── Imports ───────────────────────────── */
  import { onMount }      from "svelte";
  import { writable,
           derived       } from "svelte/store";

  import Fa               from "svelte-fa";
  import { faEdit, faList,
           faTimes,
           faToggleOff,
           faToggleOn,
           faTrash       } from "@fortawesome/free-solid-svg-icons";

  import { Splide,
           SplideSlide   } from "@splidejs/svelte-splide";
  import "@splidejs/svelte-splide/css";

  import { modlist }      from "$lib";          // ← assumed plain array.

  /* ───────────────────────────── Constants ─────────────────────────── */
  const MOBILE_BREAKPOINT = 768;                 // px – Tailwind's md breakpoint.
  const DEFAULT_ICON      = "/default_icon.png";

  /* Dummy artwork map – replace with real thumbnails later. */
  const modUiResources = {
    "CarlottaPants + Shirt NewFace": [DEFAULT_ICON, DEFAULT_ICON, DEFAULT_ICON]
  } satisfies Record<string, string[]>;

  /* ───────────────────────────── Stores ────────────────────────────── */
  /** Multiple‑selection list. */
  export const multiSelected   = writable(/** @type {Mod[]} */([]));
  /** Single selected mod (details panel). */
  export const selected        = writable(/** @type {Mod|null} */(null));

  // Filtering controls.
  const searchQuery  = writable("");          // text from search bar
  const enabledFilter = writable("all");      // "all" | "enabled" | "disabled"

  // Viewport / panel state.
  const isMobile        = writable(false);
  const showPanel       = writable(true);      // bulk‑actions panel
  const showSinglePanel = writable(false);     // single‑mod details panel

  /**
   * Derived list of mods after search + enabled filter.
   * Reactively updates whenever either store changes.
   */
  const matchedMods = derived(
    [searchQuery, enabledFilter],
    ([$q, $filter]) => {
      let list = modlist;

      // 1) Text search --------------------------------------------------
      if ($q.trim()) {
        const q = $q.toLowerCase();
        list = list.filter((m) => m.name.toLowerCase().includes(q));
      }

      // 2) Enabled state filter ----------------------------------------
      switch ($filter) {
        case "enabled":
          list = list.filter((m) => m.enabled);
          break;
        case "disabled":
          list = list.filter((m) => !m.enabled);
          break;
      }

      return list;
    },
    modlist  // <- initial value
  );

  /* ───────────────────────────── Helpers ───────────────────────────── */
  /**
   * A mod is considered a *group* when it contains more than one path whose
   * parent directory is named "SavedMods".
   * @param {Mod} mod
   */
  function isGroup(mod) {
    return mod.path.filter((p) => p.split("\\").at(-2) === "SavedMods").length > 1;
  }

  /**
   * DUMMY bulk‑action handler.
   * @param {string} action - "rename" | "delete" | "create_group" | "toggle_on" | "toggle_off"
   */
  function handle_group_action(action) { console.log(`Action: ${action}`, $multiSelected); }

  /**
   * DUMMMY single‑mod action handler.
   * @param {string} action - "rename" | "delete" | "toggle"
   * @param {Mod} mod - The mod to act on.
   */
  function handle_single_action(action, mod) { console.log(`Action: ${action}`, mod); }

  /** Quick predicate for viewport size → mobile boolean */
  const viewportIsMobile = () => window.innerWidth < MOBILE_BREAKPOINT;

  /* ───────────────────────────── Lifecycle ─────────────────────────── */
  onMount(() => {
    // Initial run ------------------------------------------------------
    const mobile = viewportIsMobile();
    isMobile.set(mobile);
    showPanel.set(!mobile);
    showSinglePanel.set(!mobile);

    // Resize listener --------------------------------------------------
    const onResize = () => {
      const mob = viewportIsMobile();
      isMobile.set(mob);
      showPanel.set(!mob);
      showSinglePanel.set(!mob);
    };

    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  });
</script>

<main class="flex flex-col h-screen w-full bg-[#181A1B] p-1">
  <!-- ─────────────────────────── Header ─────────────────────────── -->
  <header aria-label="Main header" class="mx-auto flex flex-col items-center justify-center rounded-md p-6">
    <h1 class="mb-3 text-2xl font-serif font-bold tracking-tight text-gray-100">
      <span class="italic text-indigo-300">Hyvnt's</span> WuWa Mod Manager
    </h1>
    <p class="mb-6 font-light text-gray-400">
      A stupid piece of software, done by stupid motherfucker
      <span class="italic text-indigo-200">Enjoy the suffering.</span>
      <span class="italic text-indigo-300">Sucker.</span>
    </p>
  </header>

  <!-- ─────────────────────────── Filters ─────────────────────────── -->
  <section class="mt-8 flex w-full max-w-xl flex-col items-center self-center">
    <form class="flex w-full flex-row items-center justify-between">
      <!-- Search ------------------------------------------------------- -->
      <input
        type="text"
        placeholder="Search mods..."
        bind:value={$searchQuery}
        class="w-full rounded-md border border-gray-600 bg-[#181A1B] p-3 text-gray-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        aria-label="Search mods"
      />

      <!-- Enabled filter ---------------------------------------------- -->
      <select
        bind:value={$enabledFilter}
        aria-label="Filter by mod status"
        class="ml-4 rounded border border-gray-600 bg-[#181A1B] p-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      >
        <option value="all">All</option>
        <option value="enabled">Enabled</option>
        <option value="disabled">Disabled</option>
      </select>
    </form>
  </section>

  <!-- ─────────────────────────── Mod Grid ─────────────────────────── -->
  <section class="my-4 grid max-w-3xl grid-cols-4 gap-4 self-center">
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    {#each $matchedMods as mod}
      <!-- Card wrapper ------------------------------------------------- -->
      <!-- svelte-ignore a11y_click_events_have_key_events -->
      <!-- svelte-ignore element_invalid_self_closing_tag -->
      <div
        on:click={() =>
          selected.update((s) => (s?.name === mod.name ? null : mod))
        }
        class="mod-card relative flex flex-col items-center justify-center rounded-md border border-[#3b4264] bg-[#08060c] py-2 shadow-md transition-all hover:scale-105 hover:border-[#94aee6] hover:bg-[#11111c] hover:shadow-lg"
        class:col-span-2={isGroup(mod)}
        class:border-2={$selected?.name === mod.name}
        class:border-indigo-500={$selected?.name === mod.name}
        class:bg-[#1a1a2b]={$selected?.name === mod.name}
        class:hover:bg-[#1e1e34]={$selected?.name === mod.name}
        class:hover:border-[#94aee6]={$selected?.name !== mod.name}
      >
        <!-- Card title -------------------------------------------------- -->
        <div class="mb-2 flex w-full items-center justify-between p-1" title={mod.name}>
          <h4 class="bit_text flex-1 min-w-0 overflow-hidden text-ellipsis whitespace-nowrap text-center text-lg">
            {mod.name}
          </h4>
        </div>

        <!-- Carousel --------------------------------------------------- -->
        <div class="flex h-full w-full items-center justify-center">
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
              speed: 500
            }}
          >
            {#each modUiResources[mod.name] || [DEFAULT_ICON] as resource, i}
              <SplideSlide>
                <img
                  src={resource}
                  alt={`${mod.name} icon ${i + 1}`}
                  class="h-32 w-32 rounded-md object-contain"
                />
              </SplideSlide>
            {/each}
          </Splide>
        </div>

        <!-- Enabled toggle --------------------------------------------- -->
        <button
          title={mod.enabled ? "Enabled" : "Disabled"}
          aria-label={mod.enabled ? "Enabled" : "Disabled"}
          on:click={() => {
            handle_single_action("toggle", mod);
            mod.enabled = !mod.enabled;
          }}
          class="absolute bottom-2 right-2 h-4 w-4 rounded-tl-full transition-all duration-300 hover:scale-200 hover:border-2 hover:border-gray-300"
          class:bg-green-500={mod.enabled}
          class:bg-red-500={!mod.enabled}
        />

        <!-- Multi‑select checkbox -------------------------------------- -->
        <input
          type="checkbox"
          class="select-mod-checkbox absolute top-2 left-2 h-6 w-6 appearance-none rounded-br-full border-2 border-gray-500 bg-gray-700 opacity-0 transition-all duration-300 hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 checked:border-indigo-400 checked:bg-indigo-500"
          checked={$multiSelected.includes(mod)}
          title="Select mod"
          aria-label="Select mod"
          on:change={() => {
            multiSelected.update((list) =>
              list.includes(mod) ? list.filter((m) => m !== mod) : [...list, mod]
            );
          }}
        />
      </div>
    {/each}
  </section>

  <!-- ─────────────────────── Bulk‑action Panel ─────────────────────── -->
  {#if $multiSelected.length}
    <!-- FAB (mobile) -------------------------------------------------->
    {#if $isMobile && !$showPanel}
      <button
        class="fixed bottom-4 left-4 z-50 rounded-full bg-indigo-600 p-3 text-white shadow-lg transition-colors duration-200 hover:bg-indigo-700"
        title="Toggle Mod Panel"
        aria-label="Toggle Mod Panel"
        on:click={() => {showPanel.set(true);}}
      >
        <Fa icon={faList} />
      </button>
    {/if}

    {#if $showPanel}
      <aside
        id="mod-panel"
        class="fixed left-6 top-8 z-50 h-[94vh] w-[calc(100vw-3rem)] max-w-xl rounded-xl border border-gray-700 bg-[#221f23]/60 p-4 backdrop-blur-md shadow-2xl md:max-w-md lg:max-w-xl"
      >
        <!-- Close / clear selection ---------------------------------- -->
        <button
          class="absolute right-2 top-2 text-gray-400 transition-colors hover:text-gray-200 w-5 h-5"
          title="Clear selection"
          aria-label="Clear selection"
          on:click={() => {
            multiSelected.set([]);
            showPanel.set(false);
          }}
        >
          <Fa icon={faTimes} />
        </button>

        <!-- Create group -------------------------------------------- -->
        <div class="my-4 flex flex-col space-y-2">
          <button
            class="bit_text inline-flex items-center justify-center rounded-md bg-indigo-600 p-2 text-white transition-colors duration-200 hover:bg-indigo-700"
            title="Create group from selected mods"
            aria-label="Create group from selected mods"
            on:click={() => {
              handle_group_action("create_group");
            }}
          >
            <Fa icon={faList} />
            <span class="ml-2">Create Group</span>
          </button>
        </div>
         
        <!-- Rename group --------------------------------------------- -->
        <div class="my-4 flex flex-col space-y-2">
          <button
            class="bit_text inline-flex items-center justify-center rounded-md bg-indigo-600 p-2 text-white transition-colors duration-200 hover:bg-indigo-700"
            title="Rename selected mods"
            aria-label="Rename selected mods"
            on:click={() => {
              handle_group_action("rename");
            }}
          >
            <Fa icon={faEdit} />
            <span class="ml-2">Rename Selected Mods</span>
          </button>
        </div>

        <!-- Toggle enabled state ------------------------------------- -->
        <div class="my-4 flex flex-row w-full space-x-2">
          <button
            class="bit_text inline-flex items-center justify-center rounded-md bg-green-600 p-2 text-white transition-colors duration-200 hover:bg-green-700 w-1/2"
            title="Toggle enabled state of selected mods"
            aria-label="Toggle enabled state of selected mods"
            on:click={() => {
              handle_group_action("toggle_on");
            }}
          >
            <Fa icon={faToggleOn} />
            <span class="ml-2">Enable</span>
          </button>

          <button
            class="bit_text inline-flex items-center justify-center rounded-md bg-red-600 p-2 text-white transition-colors duration-200 hover:bg-red-700 w-1/2"
            title="Disable selected mods"
            aria-label="Disable selected mods"
            on:click={() => {
              handle_group_action("toggle_off");
            }}
          >
            <Fa icon={faToggleOff} />
            <span class="ml-2">Disable</span>
          </button>
        </div>

        <!-- Danger zone ---------------------------------------------- -->
        <div class="my-8 flex flex-col space-y-2">
          <button
            class="bit_text inline-flex items-center justify-center rounded-md bg-red-600 p-2 text-white transition-colors duration-200 hover:bg-red-700"
            title="Delete selected mods"
            aria-label="Delete selected mods"
            on:click={() => {
              handle_group_action("delete");
            }}
          >
            <Fa icon={faTrash} />
            <span class="ml-2">Delete</span>
          </button>
        </div>

        <!-- Selected list -------------------------------------------- -->
        <div class="mb-4 overflow-y-auto">
          <h4 class="mb-2 text-center text-lg font-semibold text-gray-200">
            Selected Mods
          </h4>
          <ul class="list-inside list-decimal overflow-auto text-md text-gray-300">
            {#each $multiSelected as m}
              <li class="bit_text text-md">{m.name}</li>
            {/each}
          </ul>
        </div>
      </aside>
    {/if}
  {/if}

  <!-- ─────────────────────── Single‑mod Details ────────────────────── -->
  {#if $selected}
    {#if $isMobile && !$showSinglePanel}
      <button
        class="fixed bottom-4 right-4 z-50 rounded-full bg-indigo-600 p-3 text-white shadow-lg transition-colors duration-200 hover:bg-indigo-700"
        title="Toggle Mod Details"
        aria-label="Toggle Mod Details"
        on:click={() => showSinglePanel.set(true)}
      >
        <Fa icon={faList} />
      </button>
    {/if}

    {#if $showSinglePanel}
      <aside
        id="mod-details-panel"
        class="flex flex-col fixed right-6 top-8 z-50 min-w-[320px] max-w-[400px] rounded-xl border border-gray-700 bg-[#221f23]/60 p-4 backdrop-blur-md shadow-2xl"
      >
        <!-- Close ----------------------------------------------------- -->
        <button
          class="absolute right-2 top-2 text-gray-400 transition-colors hover:text-gray-200"
          title="Close details"
          aria-label="Close details"
          on:click={() => {selected.set(null); showSinglePanel.set(false)}}
        >
          <Fa icon={faTimes} />
        </button>

        <h3 class="bit_text mb-2 text-center text-xl font-bold text-gray-100">{$selected.name}</h3>


        <!-- Options -------------------------------------------- -->

        <!-- Rename -------------------------------------------- -->
        <button
          class="bit_text mb-4 inline-flex items-center justify-center rounded-md bg-indigo-600 p-2 text-white transition-colors duration-200 hover:bg-indigo-700"
          title="Rename mod"
          aria-label="Rename mod"
          on:click={() => {
            handle_single_action("rename", $selected);
          }}
        >
          <Fa icon={faEdit} />
          <span class="ml-2">Rename</span>
        </button>

        <!--Delete -------------------------------------------- -->
        <button
          class="bit_text mb-4 inline-flex items-center justify-center rounded-md bg-red-600 p-2 text-white transition-colors duration-200 hover:bg-red-700"
          title="Delete mod"
          aria-label="Delete mod"
          on:click={() => {
            handle_single_action("delete", $selected);
          }}
        >
          <Fa icon={faTrash} />
          <span class="ml-2">Delete</span>
        </button>


        <!-- Paths list ----------------------------------------------- -->
        <div class="mb-2">
          <span class="font-semibold text-gray-400 text-lg">Paths:</span>
          <ul class="list-inside list-disc text-sm text-gray-300">
            {#each $selected.path as p}
              <li class="bit_text text-sm">
                {p}
              </li>
            {/each}
          </ul>
        </div>
      </aside>
    {/if}
  {/if}
</main>

<!-- ─────────────────────────── Fonts ─────────────────────────────── -->
<svelte:head>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DotGothic16&display=swap" />
</svelte:head>

<!-- ─────────────────────────── Component CSS ─────────────────────── -->
<style>
  .bit_text {
    font-family: "DotGothic16", sans-serif;
  }

  /* Show checkbox only on card hover (or when checked) */
  .mod-card:hover .select-mod-checkbox,
  .select-mod-checkbox:checked {
    opacity: 1;
    transition: opacity 0.3s ease-in-out;
  }
</style>
