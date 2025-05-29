from bananas.recent import get_recent_mods
from bananas.search import search_mod
from bananas.shared import API_MOD_TYPE
from bananas.download import download


mods = get_recent_mods(5)


target: API_MOD_TYPE = mods[0]

print(f"Starting download for {target.name}...")

path = download(target)

print(f"Downloaded {target.name} to {path}")