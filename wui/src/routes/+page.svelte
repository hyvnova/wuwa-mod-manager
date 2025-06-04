<script lang="ts">
  /* ───────────────────────────── Type Definitions ────────────────────── */
  interface Mod {
    name: string; // Display name.
    enabled: boolean; // Current on/off state.
    path: string[]; // List of full paths that compose the mod.
  }

  interface Group {
    name: string; // Display name.
    enabled: boolean; // Current on/off state.
    members: Mod[]; // List of mods that compose the group.
  }

  // This Resource interface seems defined but not directly used as the value type in mod_resources store based on template usage.
  // The mod_resources store appears to hold Record<string, string[]> (map of mod name to list of thumbnail paths).
  // interface Resource {
  //   thumb: string[]; // List of thumbnail image paths.
  // }

  type ModOrGroup = Mod | Group;
  type Modlist = ModOrGroup[];

  interface EelService {
    py_raw_get_modlist: () => () => Promise<string>;
    py_raw_get_mod_resources: () => () => Promise<string>;
  }

  /* ───────────────────────────── Imports ───────────────────────────── */
  import { onMount } from "svelte";
  import { writable, derived } from "svelte/store";
  import type { Writable } from "svelte/store";

  import Fa from "svelte-fa";
  import {
    faEdit,
    faList,
    faTimes,
    faToggleOff,
    faToggleOn,
    faTrash,
  } from "@fortawesome/free-solid-svg-icons";

  import { Splide, SplideSlide } from "@splidejs/svelte-splide";
  import "@splidejs/svelte-splide/css";

  /* ───────────────────────────── Constants ─────────────────────────── */
  const MOBILE_BREAKPOINT = 768; // px – Tailwind's md breakpoint.
  const DEFAULT_ICON = "/default_icon.png";

  /* ───────────────────────────── Stores ────────────────────────────── */
  const modlist: Writable<Modlist> = writable([]);

  /**
   * Maps mod names to their thumbnail image paths.
   * Used for displaying mod icons in the UI.
   * Based on template usage `src={resource}`, `resource` must be a string,
   * implying `$mod_resources[mod.name]` is `string[]`.
   */
  const mod_resources: Writable<Record<string, string[]>> = writable({});

  /** Multiple‑selection list. */
  export const multiSelected: Writable<Mod[]> = writable([]);
  /** Single selected mod (details panel). */
  export const selected: Writable<Mod | null> = writable(null);

  // Filtering controls.
  const searchQuery: Writable<string> = writable(""); // text from search bar
  const enabledFilter: Writable<"all" | "enabled" | "disabled"> =
    writable("all");

  // Viewport / panel state.
  const isMobile: Writable<boolean> = writable(false);
  const showPanel: Writable<boolean> = writable(true); // bulk‑actions panel
  const showSinglePanel: Writable<boolean> = writable(false); // single‑mod details panel

  /**
   * Derived list of mods after search + enabled filter.
   * Reactively updates whenever either store changes.
   */
  const matchedMods = derived<
    [Writable<Modlist>, Writable<string>, Writable<string>],
    Modlist
  >(
    [modlist, searchQuery, enabledFilter],
    ([$modlist, $q, $filter]) => {
      let list: Modlist = $modlist;

      // 1) Text search --------------------------------------------------
      if ($q.trim()) {
        const query = $q.toLowerCase();
        list = list.filter((m) => m.name.toLowerCase().includes(query));
      }

      // 2) Enabled state filter ----------------------------------------
      switch ($filter) {
        case "all":
          break;
        case "enabled":
          list = list.filter((m) => m.enabled);
          break;
        case "disabled":
          list = list.filter((m) => !m.enabled);
          break;
      }
      return list;
    },
    [] // <- initial value
  );

  /* ───────────────────────────── Helpers ───────────────────────────── */
  /**
   * Determines if a ModOrGroup item should be displayed with group styling (e.g., wider card).
   * An item is group-like if it's an actual Group or if it's a Mod with multiple "SavedMods" paths.
   * @param item The Mod or Group item.
   */
  function isGroupLike(item: ModOrGroup): boolean {
    if ('members' in item) { // item is a Group
      return true;
    }
    // item is a Mod, check its path structure
    return (
      item.path.filter((p) => p.split("\\").at(-2) === "SavedMods").length > 1
    );
  }

  type GroupAction =
    | "rename"
    | "delete"
    | "create_group"
    | "toggle_on"
    | "toggle_off";
  /**
   * DUMMY bulk‑action handler.
   * @param action The action to perform.
   */
  function handle_group_action(action: GroupAction) {
    console.log(`Action: ${action}`, $multiSelected);
  }

  type SingleModAction = "rename" | "delete" | "toggle";
  /**
   * DUMMY single‑mod action handler.
   * @param action The action to perform.
   * @param mod The mod to act on.
   */
  function handle_single_action(action: SingleModAction, mod: Mod) {
    console.log(`Action: ${action}`, mod);
    // Actual implementation would likely involve calls to Python via eel
    // and then updating the modlist store.
    // For "toggle", the mod.enabled is already updated visually.
    // This function would handle backend persistence.
  }

  /** Quick predicate for viewport size → mobile boolean */
  const viewportIsMobile = (): boolean => window.innerWidth < MOBILE_BREAKPOINT;

  /* ───────────────────────────── Lifecycle ─────────────────────────── */
  onMount(() => {
    const eel = (window as any).eel as EelService; // Eel instance for Python comms

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

    // Comms with Python - Data/Functions
    eel.py_raw_get_modlist()()
      .then((result: string) => {
        modlist.set(JSON.parse(result) as Modlist);
      })
      .catch(error => console.error("Failed to get modlist:", error));

    eel.py_raw_get_mod_resources()()
      .then((result: string) => {
        mod_resources.set(JSON.parse(result) as Record<string, string[]>);
        // console.log("Mod resources:", JSON.parse(result));
      })
      .catch(error => console.error("Failed to get mod resources:", error));

    return () => window.removeEventListener("resize", onResize);
  });

  function handleModCardClick(modItem: ModOrGroup) {
    if ('path' in modItem) { // It's a Mod
      selected.update(currentSelectedMod =>
        currentSelectedMod?.name === modItem.name ? null : modItem
      );
    } else { // It's a Group, groups don't have a dedicated details panel in this design
      selected.set(null);
    }
  }

  function handleModToggle(event: MouseEvent, modItem: ModOrGroup) {
    event.stopPropagation(); // Prevent card click event
    
    // Optimistically update UI
    modItem.enabled = !modItem.enabled;
    
    // If it's a Mod, call the specific single_action handler
    if ('path' in modItem) { // modItem is Mod
        handle_single_action("toggle", modItem as Mod);
    } else { // modItem is Group
        // Handle group toggle if necessary, perhaps a different eel call
        console.log("Toggled group:", modItem.name, "to", modItem.enabled);
    }

    // Ensure Svelte's reactivity picks up the change if derived stores depend on item properties
    modlist.update(list => list); // or $modlist = $modlist
  }

</script>

<main class="flex flex-col h-screen w-full bg-[#181A1B] p-1">
  <!-- ─────────────────────────── Header ─────────────────────────── -->
  <header
    aria-label="Main header"
    class="mx-auto flex flex-col items-center justify-center rounded-md p-6"
  >
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
        <option value="all" selected>All</option>
        <option value="enabled">Enabled</option>
        <option value="disabled">Disabled</option>
      </select>
    </form>
  </section>

  <!-- ─────────────────────────── Mod Grid ─────────────────────────── -->
  <section class="my-4 grid max-w-3xl grid-cols-4 gap-4 self-center">
    {#each $matchedMods as mod (mod.name)}
      <!-- Card wrapper ------------------------------------------------- -->
      <!-- svelte-ignore a11y_click_events_have_key_events -->
      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <div
        role="button"
        tabindex="0"
        onclick={() => handleModCardClick(mod)}
        onkeydown={(e) => e.key === 'Enter' && handleModCardClick(mod)}
        class="mod-card relative flex flex-col items-center justify-center rounded-md border border-[#3b4264] bg-[#08060c] py-2 shadow-md transition-all hover:scale-105 hover:border-[#94aee6] hover:bg-[#11111c] hover:shadow-lg"
        class:col-span-2={isGroupLike(mod)}
        class:border-2={$selected?.name === mod.name && 'path' in mod}
        class:border-indigo-500={$selected?.name === mod.name && 'path' in mod}
        class:bg-[#1a1a2b]={$selected?.name === mod.name && 'path' in mod}
        class:hover:bg-[#1e1e34]={$selected?.name === mod.name && 'path' in mod}
        class:hover:border-[#94aee6]={$selected?.name !== mod.name || !('path' in mod)}
      >
        <!-- Card title -------------------------------------------------- -->
        <div
          class="mb-2 flex w-full items-center justify-between p-1"
          title={mod.name}
        >
          <h4
            class="bit_text flex-1 min-w-0 overflow-hidden text-ellipsis whitespace-nowrap text-center text-lg"
          >
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
              speed: 500,
            }}
          >
            {#each $mod_resources[mod.name] || [DEFAULT_ICON] as imagePath, i}
              <SplideSlide>
                <img
                  src={imagePath}
                  alt={`${mod.name} icon ${i + 1}`}
                  class="h-32 w-32 rounded-md object-contain"
                />
              </SplideSlide>
            {/each}
          </Splide>
        </div>

        <!-- Enabled toggle --------------------------------------------- -->
        <!-- svelte-ignore element_invalid_self_closing_tag -->
        <button
          title={mod.enabled ? "Enabled" : "Disabled"}
          aria-label={mod.enabled ? "Enabled" : "Disabled"}
          onclick={(event) => handleModToggle(event, mod)}
          class="absolute bottom-2 right-2 h-4 w-4 rounded-tl-full transition-all duration-300 hover:scale-200 hover:border-2 hover:border-gray-300"
          class:bg-green-500={mod.enabled}
          class:bg-red-500={!mod.enabled}
        />

        <!-- Multi‑select checkbox -------------------------------------- -->
        {#if 'path' in mod} <!-- Only show checkbox for Mods, not Groups -->
          <input
            type="checkbox"
            class="select-mod-checkbox absolute top-2 left-2 h-6 w-6 appearance-none rounded-br-full border-2 border-gray-500 bg-gray-700 opacity-0 transition-all duration-300 hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 checked:border-indigo-400 checked:bg-indigo-500"
            checked={$multiSelected.some(m => m.name === mod.name)}
            title="Select mod"
            aria-label="Select mod"
            onchange={() => {
              multiSelected.update((list) =>
                list.some((m) => m.name === (mod as Mod).name)
                  ? list.filter((m) => m.name !== (mod as Mod).name)
                  : [...list, mod as Mod]
              );
            }}
          />
        {/if}
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
        onclick={() => showPanel.set(true)}
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
          onclick={() => {
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
            onclick={() => handle_group_action("create_group")}
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
            onclick={() => handle_group_action("rename")}
          >
            <Fa icon={faEdit} />
            <span class="ml-2">Rename Selected Mods</span>
          </button>
        </div>

        <!-- Toggle enabled state ------------------------------------- -->
        <div class="my-4 flex flex-row w-full space-x-2">
          <button
            class="bit_text inline-flex items-center justify-center rounded-md bg-green-600 p-2 text-white transition-colors duration-200 hover:bg-green-700 w-1/2"
            title="Enable selected mods"
            aria-label="Enable selected mods"
            onclick={() => handle_group_action("toggle_on")}
          >
            <Fa icon={faToggleOn} />
            <span class="ml-2">Enable</span>
          </button>

          <button
            class="bit_text inline-flex items-center justify-center rounded-md bg-red-600 p-2 text-white transition-colors duration-200 hover:bg-red-700 w-1/2"
            title="Disable selected mods"
            aria-label="Disable selected mods"
            onclick={() => handle_group_action("toggle_off")}
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
            onclick={() => handle_group_action("delete")}
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
          <ul
            class="list-inside list-decimal overflow-auto text-md text-gray-300"
          >
            {#each $multiSelected as m}
              <li class="bit_text text-md">{m.name}</li>
            {/each}
          </ul>
        </div>
      </aside>
    {/if}
  {/if}

  <!-- ─────────────────────── Single‑mod Details ────────────────────── -->
  {#if $selected} <!-- $selected is Mod | null -->
    {#if $isMobile && !$showSinglePanel}
      <button
        class="fixed bottom-4 right-4 z-50 rounded-full bg-indigo-600 p-3 text-white shadow-lg transition-colors duration-200 hover:bg-indigo-700"
        title="Toggle Mod Details"
        aria-label="Toggle Mod Details"
        onclick={() => showSinglePanel.set(true)}
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
          onclick={() => {
            selected.set(null);
            showSinglePanel.set(false);
          }}
        >
          <Fa icon={faTimes} />
        </button>

        <h3 class="bit_text mb-2 text-center text-xl font-bold text-gray-100">
          {$selected.name}
        </h3>

        <!-- Options -------------------------------------------- -->

        <!-- Rename -------------------------------------------- -->
        <button
          class="bit_text mb-4 inline-flex items-center justify-center rounded-md bg-indigo-600 p-2 text-white transition-colors duration-200 hover:bg-indigo-700"
          title="Rename mod"
          aria-label="Rename mod"
          onclick={() => {
            if ($selected) handle_single_action("rename", $selected);
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
          onclick={() => {
            if ($selected) handle_single_action("delete", $selected);
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
  <link
    rel="stylesheet"
    href="https://fonts.googleapis.com/css2?family=DotGothic16&display=swap"
  />
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
