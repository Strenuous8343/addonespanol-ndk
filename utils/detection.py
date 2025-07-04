import re
from models.movie import Movie
from models.series import Series
from utils.logger import setup_logger
from utils.bd import getMetadata
from utils.fichier import get_file_info

logger = setup_logger(__name__)

def detect_quality(torrent_name):
    quality_patterns = {
        "4k": r'\b(2160|2160P|UHD|4K|DV|DOLBY VISION|HDR|HDR10|HDR10PLUS)\b',
        "1080p": r'\b(1080|1080P|FHD|FULLHD|HD|HIGHDEFINITION)\b',
        "720p": r'\b(720|720P|HD|HIGHDEFINITION)\b',
        "480p": r'\b(480P|SD|STANDARDDEFINITION)\b'
    }

    for quality, pattern in quality_patterns.items():
        if re.search(pattern, torrent_name, re.IGNORECASE):
            return quality
    return ""


def detect_quality_spec(torrent_name):
    quality_patterns = {
        "HDR": r'\b(HDR|HDR10|HDR10PLUS|HDR10PLUS|HDR10PLUS)\b',
        "DV": r'\b(DV|DOLBY VISION)\b',
        "ATMOS": r'\b(ATMOS|DOLBY ATMOS)\b',
        "TRUEHD": r'\b(TRUEHD|TRUE-HD)\b',
        "XVID": r'\b(XVID|X-VID)\b',
        "HEVC": r'\b(HEVC|H265|H.265)\b',
        "DTS": r'\b(DTS|DTS-HD)\b',
        "DDP": r'\b(DDP|DD5.1|DD7.1)\b',
        "DD": r'\b(DD|DD5.1|DD7.1)\b',
        "SDR": r'\b(SDR|SDRIP)\b',
        "WEBDL": r'\b(WEBDL|WEB-DL|WEB)\b',
        "BLURAY": r'\b(BLURAY|BLU-RAY|BD)\b',
        "DVDRIP": r'\b(DVDRIP|DVDR)\b',
        "CAM": r'\b(CAM|CAMRIP|CAM-RIP)\b',
        "TS": r'\b(TS|TELESYNC|TELESYNC)\b',
        "TC": r'\b(TC|TELECINE|TELECINE)\b',
        "R5": r'\b(R5|R5LINE|R5-LINE)\b',
        "DVDSCR": r'\b(DVDSCR|DVD-SCR)\b',
        "HDTV": r'\b(HDTV|HDTVRIP|HDTV-RIP)\b',
        "PDTV": r'\b(PDTV|PDTVRIP|PDTV-RIP)\b',
        "DSR": r'\b(DSR|DSRRIP|DSR-RIP)\b',
        "WORKPRINT": r'\b(WORKPRINT|WP)\b',
        "VHSRIP": r'\b(VHSRIP|VHS-RIP)\b',
        "VODRIP": r'\b(VODRIP|VOD-RIP)\b',
        "TVRIP": r'\b(TVRIP|TV-RIP)\b',
        "WEBRIP": r'\b(WEBRIP|WEB-RIP)\b',
        "BRRIP": r'\b(BRRIP|BR-RIP)\b',
        "BDRIP": r'\b(BDRIP|BD-RIP)\b',
        "HDCAM": r'\b(HDCAM|HD-CAM)\b',
        "HDRIP": r'\b(HDRIP|HD-RIP)\b',
        "AAC": r'\b(AAC|AAC5.1|AAC2.0)\b',
        "EAC3": r'\b(EAC3|EAC3 5.1|EAC3 7.1)\b',
        "MP3": r'\b(MP3|MP3 2.0|MP3 5.1)\b',
        "FLAC": r'\b(FLAC|FLAC 5.1|FLAC 7.1)\b',
        "OPUS": r'\b(OPUS|OPUS 5.1|OPUS 7.1)\b',
        "DTSHD": r'\b(DTS-HD|DTS-HD MA)\b',
    }

    qualities = []
    for quality, pattern in quality_patterns.items():
        if re.search(pattern, torrent_name, re.IGNORECASE):
            qualities.append(quality)
    return qualities if qualities else None


def detect_languages(torrent_name):
    language_patterns = {
        "fr": r'\b(FRENCH|FR|VF|VF2|VFF|TRUEFRENCH|VFQ|FRA)\b',
        "en": r'\b(ENGLISH|EN|ENG)\b',
        "es": r'\b(SPANISH|ES|ESP|SPA|spa)\b',
        "de": r'\b(GERMAN|DE|GER)\b',
        "it": r'\b(ITALIAN|IT|ITA)\b',
        "pt": r'\b(PORTUGUESE|PT|POR)\b',
        "ru": r'\b(RUSSIAN|RU|RUS)\b',
        "in": r'\b(INDIAN|IN|HINDI|TELUGU|TAMIL|KANNADA|MALAYALAM|PUNJABI|MARATHI|BENGALI|GUJARATI|URDU|ODIA|ASSAMESE|KONKANI|MANIPURI|NEPALI|SANSKRIT|SINHALA|SINDHI|TIBETAN|BHOJPURI|DHIVEHI|KASHMIRI|KURUKH|MAITHILI|NEWARI|RAJASTHANI|SANTALI|SINDHI|TULU)\b',
        "nl": r'\b(DUTCH|NL|NLD)\b',
        "hu": r'\b(HUNGARIAN|HU|HUN)\b',
        "la": r'\b(LATIN|LATINO|LA)\b',
        "multi": r"\b(MULTI)\b"
    }

    languages = []
    for language, pattern in language_patterns.items():
        if re.search(pattern, torrent_name, re.IGNORECASE):
            languages.append(language)

    if re.search(r'\bMULTI\b', torrent_name, re.IGNORECASE):
        languages.append("multi")

    if len(languages) == 0:
        return ["en"]

    return languages

def post_process_results(link, media, debrid_service, url, result=None):
    # Si result es None, inicializamos el diccionario
    if result is None:
        result = {}

    result['link'] = link
    result['url'] = url
    result['media'] = media
    result['debrid_service'] = debrid_service
    result['playback'] = url
    result['filename'] = getMetadata(link, media.type)
    
    # Detectar y asignar idiomas, calidad y especificaciones si no existen
    result['languages'] = detect_languages(result['filename']) if 'languages' not in result else result['languages']
    result['quality_spec'] = detect_quality_spec(result['filename']) if 'quality_spec' not in result else result['quality_spec']
    result['type'] = media.type

    # Si el medio es una serie, añadir temporada y episodio
    if isinstance(media, Series):
        result['season'] = media.season if 'season' not in result else result['season']
        result['episode'] = media.episode if 'episode' not in result else result['episode']

    return result

