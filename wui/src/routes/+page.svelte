<script>
  import { onMount } from "svelte";
  import Fa from 'svelte-fa'
  import { faTrash } from '@fortawesome/free-solid-svg-icons';
  import { Splide, SplideSlide } from '@splidejs/svelte-splide';
  import '@splidejs/svelte-splide/css';


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
      let memebers = mod.path.filter(p => {
          const segments = p.split("\\");
          return segments[segments.length - 2] === "SavedMods";
      });
      return memebers.length > 1;
  }


</script>

<main class="flex flex-col p-1 w-full h-screen bg-[#181A1B]">
  <!-- Main content area -->
  <header
    class="content p-6 rounded-md flex flex-col mx-auto justify-center items-center " 
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
  <!--
    A grid of mod cards
  -->
  <div class="grid grid-cols-4 gap-4 self-center mt-8 max-w-3xl">
    {#each modlist as mod}
      <div
        class="bg-[#08060c] border-[#3b4264]
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
                type: 'loop',
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

      </div>
    {/each}
  </div>
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
</style>
