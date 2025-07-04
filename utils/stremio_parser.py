from utils.logger import setup_logger


logger = setup_logger(__name__)

INSTANTLY_AVAILABLE = "[⚡]"
DOWNLOAD_REQUIRED = "[⬇️]"
DIRECT_TORRENT = "[🏴‍☠️]"


def get_emoji(language):
    emoji_dict = {
        "fr": "🇫🇷",
        "en": "🇬🇧",
        "es": "🇪🇸",
        "de": "🇩🇪",
        "it": "🇮🇹",
        "pt": "🇵🇹",
        "ru": "🇷🇺",
        "in": "🇮🇳",
        "nl": "🇳🇱",
        "hu": "🇭🇺",
        "la": "🇲🇽",
        "multi": "🌍"
    }
    return emoji_dict.get(language, "🇪🇸")


def parse_to_debrid_stream(stream_list: list, config, media, nombre_debrid, fichier_is_up: bool = True):
    updated_list = []
    for link in stream_list:

        addon_title = ""
        if nombre_debrid == "RealDebrid":
            if "1fichier" in link.get('link', ''):
                addon_title = "[RD+ ✅]" if fichier_is_up else "[RD Download 🔴]"
            else:
                addon_title = "[RD+ ✅]"
        elif nombre_debrid == "AllDebrid":
            addon_title = "[AD+]"

        if media.type == "movie":
            title_desc = f"{media.titles[0]} - "
        elif media.type == "series":
            title_desc = f"{media.titles[0]} S{media.season}E{media.episode} - "

        if link.get('quality') == "4k":
            title_desc += "2160p "
        else:
            title_desc += link.get('quality', 'Unknown') + " "

        quality_tag = f"{link.get('quality', '')}"
        resolution = f"{quality_tag}"
        quality_spec = link.get('quality_spec', [])
        if quality_spec and quality_spec[0] not in ["Unknown", ""]:
            title_desc += f"({'|'.join(quality_spec)})"

        size_in_gb = round(int(link['filesize']) / 1024 / 1024 / 1024, 2)
        description = f"{title_desc}\n💾 {size_in_gb}GB\n"

        for language in link.get('languages', []):
            description += f"{get_emoji(language)}/"
        description = description.rstrip('/')  # Elimina el último "/"

        if config.get('debrid'):
            spacer = "\u2800" * 5
            title = f"[RD+ ✅] NDK{spacer} {resolution}"
            entry = {
                "name": title,
                "url": link['playback'],
                "description": description,
                "size_in_gb": size_in_gb,
                "behaviorHints": {
                    "notWebReady": not link.get('streamable', False),
                    "filename": title_desc,
                    "videoSize": int(link['filesize']),
                    "bingeGroup": f"NDK | {media.type}_{media.id}_{resolution}",
                },
            }
            updated_list.append(entry)

    # Ordenamos la lista actualizada por tamaño (descendente)
    updated_list.sort(key=lambda x: x['size_in_gb'], reverse=True)

    # Reemplazamos el contenido original de stream_list
    stream_list[:] = updated_list
