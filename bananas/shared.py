from attr import dataclass


URL = "https://gamebanana.com/games/20357"  # Wuthering Waves
GAME_ID = 20357
INDEX_EP = "https://gamebanana.com/apiv10/Mod/Index"
DATA_EP = "https://api.gamebanana.com/Core/Item/Data"
FIELDS = "name,Url().sProfileUrl(),Preview().sStructuredDataFullsizeUrl()"
MAX_PER = 50  # API limit


@dataclass
class API_MOD_TYPE:
    name: str
    link: str
    thumb: str
    date: int # Unix timestamp, used as a sort of version number
    id: int 