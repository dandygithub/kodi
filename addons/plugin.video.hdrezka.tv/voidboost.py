import re
import base64
import logging
from operator import itemgetter
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

BK_SEP = '//_//'
BK_BLOCKS = [
    'JCQhIUAkJEBeIUAjJCRA',
    'QEBAQEAhIyMhXl5e',
    'IyMjI14hISMjIUBA',
    'Xl5eIUAjIyEhIyM=',
    'JCQjISFAIyFAIyM='
]

# Компилируем один раз
QUALITY_PATTERN = re.compile(r'\[((\d+)[^]]+)].+?(http.+?mp4)', re.DOTALL)


def parse_streams(data: str) -> List[Tuple[str, int, str]]:
    """
    Парсит потоки из обфусцированной или plain text строки.
    Сохраняет оригинальную логику: берет первый URL после качества.

    Returns:
        [(quality_name, quality_int, url), ...] отсортировано по качеству desc

    Raises:
        ValueError: Если нет валидных потоков
    """
    if not isinstance(data, str) or not data.strip():
        raise ValueError("Input must be non-empty string")

    # Шаг 1: Очистка (как в оригинале)
    cleaned = _clean_obfuscation(data)

    # Шаг 2: Декодирование с автоопределением формата
    decoded = _decode(cleaned)
    if not decoded:
        raise ValueError("Failed to decode streams data")

    # Шаг 3: Парсинг (оригинальная логика)
    streams = _parse_quality_blocks(decoded)

    if not streams:
        logger.warning(f"No streams parsed from: {decoded[:200]}...")
        raise ValueError("No streams found in decoded data")

    # Шаг 4: Сортировка (оригинальная)
    return sorted(streams, key=itemgetter(1), reverse=True)


def _clean_obfuscation(data: str) -> str:
    """Удаляет escape-символы и мусорные блоки."""
    result = data.replace('\\', '')
    for block in BK_BLOCKS:
        result = result.replace(BK_SEP + block, '')
    return result


def _decode(data: str) -> Optional[str]:
    """
    Определяет формат и декодирует.
    Plain text: начинается с [
    Base64: остальное
    """
    # Plain text (новый формат без обфускации)
    if data.startswith('['):
        logger.debug("Detected plain text format")
        return data

    # Base64 (старый формат)
    try:
        # Проверяем минимальную длину для base64
        if len(data) < 4:
            return None

        decoded_bytes = base64.b64decode(data[2:])
        return decoded_bytes.decode('utf-8')
    except (ValueError, UnicodeDecodeError) as e:
        logger.debug(f"Base64 decode failed: {e}")
        return None


def _parse_quality_blocks(decoded: str) -> List[Tuple[str, int, str]]:
    """
    Парсит блоки [quality]url.
    Сохраняет оригинальное поведение: берет первый http...mp4 после [quality].
    """
    streams = []

    for match in QUALITY_PATTERN.finditer(decoded):
        quality_name = match.group(1)  # "1080p" или "1080p Ultra"
        quality_num = int(match.group(2))  # 1080
        url = match.group(3)  # http...mp4 (первый найденный после [quality])

        # Валидация URL
        if _is_valid_url(url):
            # Очистка HLS-суффикса для совместимости
            clean_url = url.replace(':hls:manifest.m3u8', '')
            streams.append((quality_name, quality_num, clean_url))
        else:
            logger.warning(f"Invalid URL parsed: {url[:100]}...")

    return streams


def _is_valid_url(url: str) -> bool:
    """Проверяет что URL начинается с http и содержит домен."""
    return (
        url.startswith(('http://', 'https://')) and
        len(url) > 10 and
        '.' in url[8:]  # после http:// или https://
    )