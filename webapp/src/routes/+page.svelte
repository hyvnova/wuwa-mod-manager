<script lang="ts">
	/* ───────────────────────────── Imports ───────────────────────────── */
	// This file is the brain and the face. If something feels dumb, it's probably because it is. Suffer.
	import { onMount } from 'svelte';
	import { derived, writable } from 'svelte/store';
	import type { Readable, Writable } from 'svelte/store';

	import {
		rebuild_modlist,
		handle_action,
		handleOutputFn,
		is_group,
		handleModlistUpdate,
		handleInputFn
	} from '$lib';
	import { eel, getting_input, mod_resources, modlist, show_log_panel } from '$store/data';

	import type { Eel } from '$lib/types';
	import {
		faCog,
		faEdit,
		faList,
		faTimes,
		faToggleOff,
		faToggleOn,
		faTrash
	} from '@fortawesome/free-solid-svg-icons';
	import Fa from 'svelte-fa';
	import { messages } from '$store/messages';
	import { Splide, SplideSlide } from '@splidejs/svelte-splide';
	import '@splidejs/svelte-splide/css';
	import {
		Action,
		type GroupObject,
		type Item,
		type ModList,
		type ModObject,

		type ModResources

	} from '$lib/bisextypes';

	/* ───────────────────────────── Constants ─────────────────────────── */
	const MOBILE_BREAKPOINT = 768; // px – Tailwind's md breakpoint.

	/** Multiple‑selection list. */
	export const multiSelected: Writable<ModObject[]> = writable([]);
	/** Single selected mod (details panel). */
	export const selected: Writable<Item | null> = writable(null);

	// Filtering controls.
	const searchQuery: Writable<string> = writable(''); // text from search bar
	const enabledFilter: Writable<'all' | 'enabled' | 'disabled'> = writable('all');

	// Viewport / panel state.
	const isMobile: Writable<boolean> = writable(false);
	const showPanel: Writable<boolean> = writable(true); // bulk‑actions panel
	const showSinglePanel: Writable<boolean> = writable(false); // single‑mod details panel

	/**
	 * Derived list of mods after search + enabled filter.
	 * Reactively updates whenever either store changes.
	 *
	 * Why? Because users are lazy and type like goblins, so we filter and search for them.
	 */
	const matchedMods: Readable<ModList> = derived<
		[Writable<ModList>, Writable<string>, Writable<string>],
		ModList
	>(
		[modlist, searchQuery, enabledFilter],
		([$modlist, $q, $filter]) => {
			let list: ModList = $modlist;

			// 1) Text search --------------------------------------------------
			if ($q.trim()) {
				const query = $q.toLowerCase();
				list = list.filter((m) => m.name.toLowerCase().includes(query));
			}

			// 2) Enabled state filter ----------------------------------------
			switch ($filter) {
				case 'all':
					break;
				case 'enabled':
					list = list.filter((m) => m.enabled);
					break;
				case 'disabled':
					list = list.filter((m) => !m.enabled);
					break;
			}
			return list;
		},
		[] // <- initial value
	);

	/** Quick predicate for viewport size → mobile boolean */
	const viewportIsMobile = (): boolean => window.innerWidth < MOBILE_BREAKPOINT;

	/* ───────────────────────────── BRAIN ─────────────────────────── */
	// This is the boot-up brain dump. Sets up eel, input/output, and resizes. If you break this, the app dies.
	onMount(() => {
		const local_eel = (window as any).eel as Eel;

		eel.set(local_eel); // Set Eel instance for global access

		handleInputFn();
		handleOutputFn();
		handleModlistUpdate();

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

		window.addEventListener('resize', onResize);

		// Comms with Python - Data/Functions
		// If this fails, blame eel or your own stupidity.
		local_eel
			.py_raw_get_modlist()()
			.then((result: string) => {
				modlist.set(JSON.parse(result) as ModList);
			})
			.catch((error) => console.error('Failed to get modlist:', error));

		local_eel
			.py_raw_get_mod_resources()()
			.then((result: string) => {
				mod_resources.set(JSON.parse(result) as ModResources);
				// console.log("Mod resources:", JSON.parse(result));
			})
			.catch((error) => console.error('Failed to get mod resources:', error));

		/**
		 * If log panel it's open,
		 * When Enter or Escape is pressed, close it.
		 *
		 * Why? Because users panic and mash keys. This is the mercy exit.
		 */
		const handleKeydown = (event: KeyboardEvent) => {
			if ($show_log_panel && (event.key === 'Enter' || event.key === 'Escape')) {
				show_log_panel.set(false);
			}
		};
		window.addEventListener('keydown', handleKeydown);

		return () => {
			window.removeEventListener('resize', onResize);
			window.removeEventListener('keydown', handleKeydown);
		};
	});

	/* ───────────────────────────── Constants ───────────────────────────── */
	const DEFAULT_ICON = '/default_icon.png';

	/* ───────────────────────────── Functions ────────────────────────────── */

	function handleModCardClick(modItem: Item) {
		// This is the single-select princess click. Only one mod gets the spotlight.
		selected.update((current) => {
			return modItem;
		});
	}

	function handleModToggle(event: MouseEvent, modItem: Item) {
		event.stopPropagation(); // Don't let the click bubble, or you'll open the details panel like a fool.

		handle_action(Action.Toggle, [modItem]);

		// Optimistically update UI. If Python fails, that's your problem.
		modItem.enabled = !modItem.enabled;

		// Svelte is dumb about object mutation, so force an update.
		modlist.update((list) => list); // or $modlist = $modlist
	}

	function handleModDelete(event: MouseEvent, modItem: Item) {
		event.stopPropagation(); // Don't let the click bubble, or you'll open the details panel like a fool.

		handle_action(Action.Delete, [modItem]);

		// Optimistically update UI. If Python fails, that's your problem.
		modlist.update((list) => list.filter(m => m.name !== modItem.name));
		
		// Clear selection if this was the selected item
		if ($selected?.name === modItem.name) {
			selected.set(null);
		}
		
		// Remove from multi-selection if it was selected
		multiSelected.update(list => list.filter(m => m.name !== modItem.name));
	}

	getting_input.subscribe((getting) => {
		if (getting) {
			show_log_panel.set(true);
			let val = prompt('Enter input:');
			if (val !== null) {
				$eel.py_get_input(val);
			} else {
				getting_input.set(false);
			}
		} else {
			show_log_panel.set(false);
		}
	});
</script>

<main class="flex flex-col min-h-screen w-full bg-bg p-4 md:p-8">
	<!-- ─────────────────────────── Header ─────────────────────────── -->
	<header
		aria-label="Main header"
		class="mx-auto flex flex-col items-center justify-center rounded-retro-lg p-8 bg-surface/40 backdrop-blur-sm border border-border/20 shadow-retro"
	>
		<h1 class="mb-4 text-3xl font-serif font-bold tracking-tight text-text-primary">
			<span class="italic text-accent">Hyvnt's</span> WuWa Mod Manager
		</h1>
		<p class="mb-6 font-light text-text-secondary text-lg">
			A stupid piece of software, done by stupid motherfucker
			<span class="italic text-accent/80">Enjoy the suffering.</span>
			<span class="italic text-accent/60">Sucker.</span>
		</p>
	</header>

	<!-- ─────────────────────────── Special Options ────────────────────────── -->
	<section class="flex w-full max-w-2xl flex-col items-center self-center mt-8">
		<div class="mb-6 flex w-full flex-row items-center justify-between">
			<!-- Rebuild Modlist -->
			<button
				class="inline-flex items-center justify-center rounded-retro bg-surface-2 px-4 py-2 text-text-primary transition-all duration-200 hover:bg-accent/20 hover:text-accent border border-border/20 shadow-retro"
				title="Rebuild modlist"
				aria-label="Rebuild modlist"
				onclick={rebuild_modlist}
			>
				<Fa icon={faCog} class="text-lg" />
				<span class="ml-2 font-medium">Rebuild Modlist</span>
			</button>
		</div>
	</section>

	<!-- ─────────────────────────── Filters ─────────────────────────── -->
	<section class="mt-8 flex w-full max-w-2xl flex-col items-center self-center">
		<form class="flex w-full flex-row items-center justify-between gap-4">
			<!-- Search ------------------------------------------------------- -->
			<input
				type="text"
				placeholder="Search mods..."
				bind:value={$searchQuery}
				class="w-full rounded-retro border border-border/20 bg-surface/40 p-3 text-text-primary placeholder-text-muted focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50 transition-all duration-200 shadow-retro"
				aria-label="Search mods"
			/>

			<!-- Enabled filter ---------------------------------------------- -->
			<select
				bind:value={$enabledFilter}
				aria-label="Filter by mod status"
				class="rounded-retro border border-border/20 bg-surface/40 p-3 text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent/50 transition-all duration-200 shadow-retro"
			>
				<option value="all" selected>All</option>
				<option value="enabled">Enabled</option>
				<option value="disabled">Disabled</option>
			</select>
		</form>
	</section>

	<!-- MAIN CONTENT -->
	{#if $show_log_panel}
		<!-- Log Output Section -->
		<section
			class="content bg-surface/40 p-8 rounded-retro-lg shadow-retro-lg flex flex-col overflow-auto relative border border-border/20 backdrop-blur-sm"
		>
			<!-- Close (X) button -->
			<button
				class="absolute top-4 right-4 text-text-secondary hover:text-text-primary transition-colors duration-200 z-10"
				title="Close log"
				aria-label="Close log"
				onclick={() => show_log_panel.set(false)}
			>
				<Fa icon={faTimes} class="text-xl" />
			</button>
			<div
				class="overflow-y-auto flex-1 bg-surface-2/40 p-6 rounded-retro shadow-retro flex flex-col items-center border border-border/20"
			>
				{#each $messages as message}
					<div
						class="message typing-effect
						min-h-[30px]
						h-auto
						px-4 py-2
						bg-surface/40 text-text-primary
						font-mono text-lg
						shadow-retro
						border-x border-border/20
						w-full text-center"
					>
						{message}
					</div>
				{/each}
			</div>
		</section>
	{:else}
		<!-- ─────────────────────────── Mod Grid ─────────────────────────── -->
		<section class="my-8 grid max-w-4xl grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 self-center">
			{#each $matchedMods as mod (mod.name)}
				<!-- Card wrapper ------------------------------------------------- -->
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					role="button"
					tabindex="0"
					onclick={() => handleModCardClick(mod)}
					onkeydown={(e) => e.key === 'Enter' && handleModCardClick(mod)}
					class="mod-card relative flex flex-col items-center justify-center rounded-retro border border-border/20 bg-surface/40 p-4 shadow-retro transition-all duration-300 hover:scale-[1.02] hover:border-accent/50 hover:bg-surface-2/40 hover:shadow-retro-lg {is_group(mod) ? 'col-span-2' : ''} {$selected?.name === mod.name ? 'border-2 border-accent bg-surface-3/60 hover:bg-surface-3/80' : 'hover:border-accent'}"
				>
					<div class="mb-3 flex w-full items-center justify-between p-1" title={mod.name}>
						<h4
							class="bit_text flex-1 min-w-0 overflow-hidden text-ellipsis whitespace-nowrap text-center text-lg font-medium text-text-primary"
						>
							{mod.name}
						</h4>
					</div>

					<!-- Carousel --------------------------------------------------- -->
					<div class="flex h-full w-full items-center justify-center">
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
								speed: 500
							}}
						>
							{#each $mod_resources[mod.name]?.thumb || [DEFAULT_ICON] as imagePath, i}
								<SplideSlide>
									<img
										src={imagePath}
										alt={`${mod.name} icon ${i + 1}`}
										class="h-32 w-32 rounded-retro object-contain"
									/>
								</SplideSlide>
							{/each}
						</Splide>
					</div>

					<!-- Enabled toggle --------------------------------------------- -->
					<!-- svelte-ignore element_invalid_self_closing_tag -->
					<button
						title={mod.enabled ? 'Enabled' : 'Disabled'}
						aria-label={mod.enabled ? 'Enabled' : 'Disabled'}
						onclick={(event) => handleModToggle(event, mod)}
						class="absolute bottom-3 right-3 h-4 w-4 rounded-tl-full transition-all duration-300 hover:scale-200 hover:border-2 hover:border-border"
						class:bg-success={mod.enabled}
						class:bg-error={!mod.enabled}
					/>

					<!-- Multi‑select checkbox -------------------------------------- -->
					{#if 'path' in mod}
						<!-- Only show checkbox for Mods, not Groups -->
						<input
							type="checkbox"
							class="select-mod-checkbox absolute top-3 left-3 h-5 w-5 appearance-none rounded-br-full border-2 border-border bg-surface-2 opacity-0 transition-all duration-300 hover:bg-accent/20 focus:outline-none focus:ring-2 focus:ring-accent/50 checked:border-accent checked:bg-accent/40"
							checked={$multiSelected.some((m) => m.name === mod.name)}
							title="Select mod"
							aria-label="Select mod"
							onchange={() => {
								multiSelected.update((list) =>
									list.some((m) => m.name === (mod as ModObject).name)
										? list.filter((m) => m.name !== (mod as ModObject).name)
										: [...list, mod as ModObject]
								);
							}}
						/>
					{/if}
				</div>
			{/each}
		</section>
	{/if}

	<!-- ─────────────────────── Multi Panel ─────────────────────── -->
	{#if $multiSelected.length}
		<!-- FAB (mobile) -------------------------------------------------->
		{#if $isMobile && !$showPanel}
			<button
				class="fixed bottom-6 left-6 z-50 rounded-full bg-surface-2 p-4 text-text-primary shadow-retro-lg transition-all duration-300 hover:bg-accent/20 hover:text-accent border border-border/20"
				title="Toggle Mod Panel"
				aria-label="Toggle Mod Panel"
				onclick={() => showPanel.set(true)}
			>
				<Fa icon={faList} class="text-xl" />
			</button>
		{/if}

		{#if $showPanel}
			<aside
				id="mod-panel"
				class="fixed left-6 top-8 z-50 h-[94vh] w-[calc(100vw-3rem)] max-w-xl rounded-retro-lg border border-border/20 bg-surface/40 p-6 backdrop-blur-md shadow-retro-lg md:max-w-md lg:max-w-xl"
			>
				<!-- Close / clear selection ---------------------------------- -->
				<button
					class="absolute right-4 top-4 text-text-secondary hover:text-text-primary transition-colors duration-200 w-6 h-6"
					title="Clear selection"
					aria-label="Clear selection"
					onclick={() => {
						multiSelected.set([]);
					}}
				>
					<Fa icon={faTimes} class="text-xl" />
				</button>

				<!-- Create group -------------------------------------------- -->
				<div class="my-6 flex flex-col space-y-3">
					<button
						class="bit_text inline-flex items-center justify-center rounded-retro bg-surface-2 px-4 py-2 text-text-primary transition-all duration-200 hover:bg-accent/20 hover:text-accent border border-border/20 shadow-retro"
						title="Create group from selected mods"
						aria-label="Create group from selected mods"
						onclick={() => handle_action(Action.CreateGroup, $multiSelected)}
					>
						<Fa icon={faList} class="text-lg" />
						<span class="ml-2 font-medium">Create Group</span>
					</button>
				</div>

				<!-- Rename group --------------------------------------------- -->
				<div class="my-6 flex flex-col space-y-3">
					<button
						class="bit_text inline-flex items-center justify-center rounded-retro bg-surface-2 px-4 py-2 text-text-primary transition-all duration-200 hover:bg-accent/20 hover:text-accent border border-border/20 shadow-retro"
						title="Rename selected mods"
						aria-label="Rename selected mods"
						onclick={() => handle_action(Action.Rename, $multiSelected)}
					>
						<Fa icon={faEdit} class="text-lg" />
						<span class="ml-2 font-medium">Rename Selected Mods</span>
					</button>
				</div>

				<!-- Toggle enabled state ------------------------------------- -->
				<div class="my-6 flex flex-row w-full space-x-3">
					<button
						class="bit_text inline-flex items-center justify-center rounded-retro bg-surface-2 px-4 py-2 text-text-primary transition-all duration-200 hover:bg-success/20 hover:text-success border border-border/20 shadow-retro w-1/2"
						title="Enable selected mods"
						aria-label="Enable selected mods"
						onclick={() => handle_action(Action.Enable, $multiSelected)}
					>
						<Fa icon={faToggleOn} class="text-lg" />
						<span class="ml-2 font-medium">Enable</span>
					</button>

					<button
						class="bit_text inline-flex items-center justify-center rounded-retro bg-surface-2 px-4 py-2 text-text-primary transition-all duration-200 hover:bg-error/20 hover:text-error border border-border/20 shadow-retro w-1/2"
						title="Disable selected mods"
						aria-label="Disable selected mods"
						onclick={() => handle_action(Action.Disable, $multiSelected)}
					>
						<Fa icon={faToggleOff} class="text-lg" />
						<span class="ml-2 font-medium">Disable</span>
					</button>
				</div>

				<!-- Danger zone ---------------------------------------------- -->
				<div class="my-8 flex flex-col space-y-3">
					<button
						class="bit_text inline-flex items-center justify-center rounded-retro bg-surface-2 px-4 py-2 text-text-primary transition-all duration-200 hover:bg-error/20 hover:text-error border border-border/20 shadow-retro"
						title="Delete selected mods"
						aria-label="Delete selected mods"
						onclick={() => handle_action(Action.Delete, $multiSelected)}
					>
						<Fa icon={faTrash} class="text-lg" />
						<span class="ml-2 font-medium">Delete</span>
					</button>
				</div>

				<!-- Selected list -------------------------------------------- -->
				<div class="mb-4 overflow-y-auto">
					<h4 class="mb-3 text-center text-lg font-semibold text-text-primary">Selected Mods</h4>
					<ul class="list-inside list-decimal overflow-auto text-md text-text-secondary">
						{#each $multiSelected as m}
							<li class="bit_text text-md">{m.name}</li>
						{/each}
					</ul>
				</div>
			</aside>
		{/if}
	{/if}

	<!-- ─────────────────────── Single Panel  ────────────────────── -->
	{#if $selected}
		<!-- $selected is Mod | null -->
		{#if $isMobile && !$showSinglePanel}
			<button
				class="fixed bottom-6 right-6 z-50 rounded-full bg-surface-2 p-4 text-text-primary shadow-retro-lg transition-all duration-300 hover:bg-accent/20 hover:text-accent border border-border/20"
				title="Toggle Mod Details"
				aria-label="Toggle Mod Details"
				onclick={() => showSinglePanel.set(true)}
			>
				<Fa icon={faList} class="text-xl" />
			</button>
		{/if}

		{#if $showSinglePanel}
			<aside
				id="mod-details-panel"
				class="flex flex-col fixed right-6 top-8 z-50 min-w-[320px] max-w-[400px] rounded-retro-lg border border-border/20 bg-surface/40 p-6 backdrop-blur-md shadow-retro-lg"
			>
				<!-- Close ----------------------------------------------------- -->
				<button
					class="absolute right-4 top-4 text-text-secondary hover:text-text-primary transition-colors duration-200"
					title="Close details"
					aria-label="Close details"
					onclick={() => {
						selected.set(null);
					}}
				>
					<Fa icon={faTimes} class="text-xl" />
				</button>

				<h3 class="bit_text mb-4 text-center text-2xl font-bold text-text-primary">
					{$selected.name}
				</h3>

				<!-- [ Options ]  -->

				<!-- Rename -------------------------------------------- -->
				<button
					class="bit_text mb-4 inline-flex items-center justify-center rounded-retro bg-surface-2 px-4 py-2 text-text-primary transition-all duration-200 hover:bg-accent/20 hover:text-accent border border-border/20 shadow-retro"
					title="Rename mod"
					aria-label="Rename mod"
					onclick={(event) => {
						handle_action(Action.Rename, $selected);
					}}
				>
					<Fa icon={faEdit} class="text-lg" />
					<span class="ml-2 font-medium">Rename</span>
				</button>

				<!--Delete -------------------------------------------- -->
				<button
					class="bit_text mb-6 inline-flex items-center justify-center rounded-retro bg-surface-2 px-4 py-2 text-text-primary transition-all duration-200 hover:bg-error/20 hover:text-error border border-border/20 shadow-retro"
					title="Delete mod"
					aria-label="Delete mod"
					onclick={(event) => $selected && handleModDelete(event, $selected)}
				>
					<Fa icon={faTrash} class="text-lg" />
					<span class="ml-2 font-medium">Delete</span>
				</button>

				<!-- Details -->
				<div class="mb-2">
					<span class="font-semibold text-text-secondary text-lg">
						{#if is_group($selected)}
							Group Members:
						{:else}
							Mod Paths:
						{/if}
					</span>
					<ul class="list-inside list-disc text-sm text-text-secondary mt-2">
						<!-- Group detail : members -->
						{#if is_group($selected)}
							{#each ($selected as GroupObject).members as m}
								<li class="bit_text text-sm">
									{m.name}
								</li>
							{/each}
						{:else}
							<!-- Mod detail : paths -->
							{#each ($selected as ModObject).path as p}
								<li class="bit_text text-sm">
									{p}
								</li>
							{/each}
						{/if}
					</ul>
				</div>
			</aside>
		{/if}
	{/if}
</main>
