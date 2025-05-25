import re

with open(r"main.py", "r", encoding="utf-8") as f:
    content = f.read()

pattern = re.compile(
    r"(def is_valid_mod_folder\(folder: Path\)[\s\S]+?)(?=\ndef |\n#|def validate_and_collect|\Z)", re.MULTILINE
)
replacement = '''
def is_valid_mod_folder(folder: Path) -> Tuple[FolderValidation, Dict[str, List[Path]]]:
    """
    Regla:
    - Si la carpeta actual contiene uno o más .ini, es SINGLE_MOD (toma todos los subpaths con .ini descendientes).
    - Si no, pero contiene varias subcarpetas, y esas subcarpetas contienen .ini, es MULTI_MODS.
    - Si no hay .ini en ningún sitio relevante, es NOT_MOD.
    """
    if not folder.is_dir():
        return FolderValidation.NOT_MOD, {}

    # Caso 1: la propia raíz tiene .ini
    if any(f.is_file() and f.suffix == ".ini" for f in folder.iterdir()):
        # Recoge todas las carpetas descendientes (incluida la raíz) que tengan .ini
        paths_with_ini = set()
        for entry in folder.rglob("*.ini"):
            if entry.parent.is_dir():
                paths_with_ini.add(entry.parent)
        return FolderValidation.SINGLE_MOD, {folder.name: list(paths_with_ini)}

    # Caso 2: revisar subcarpetas directas
    subdirs = [d for d in folder.iterdir() if d.is_dir()]
    children = {}
    for sub in subdirs:
        # Sólo cuenta como mod si hay .ini directo en la subcarpeta
        if any(f.is_file() and f.suffix == ".ini" for f in sub.iterdir()):
            children[sub.name] = [sub]

    if not children:
        return FolderValidation.NOT_MOD, {}

    if len(children) == 1:
        return FolderValidation.SINGLE_MOD, children
    else:
        return FolderValidation.MULTI_MODS, children
'''.lstrip("\n")

new_content, n = pattern.subn(replacement, content, count=1)

with open(r"main.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Reemplazo realizado: {n} función(es) modificada(s).")