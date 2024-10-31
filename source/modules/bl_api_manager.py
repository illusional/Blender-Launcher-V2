import json
import logging
import sys
from functools import lru_cache
from pathlib import Path

from modules._platform import get_config_path, get_cwd, get_platform

logger = logging.getLogger()

config_path = Path(get_config_path())
bl_api_path = config_path / "Blender Launcher API.json"
stable_build_path = config_path / "stable_builds.json"

if getattr(sys, "frozen", False):
    internal_bl_api_path = Path(sys._MEIPASS) / "files/blender_launcher_api.json"  # noqa: SLF001
    internal_stable_build_path = Path(sys._MEIPASS) / f"files/stable_builds_api_{get_platform().lower()}.json"  # noqa: SLF001
else:
    internal_bl_api_path = Path("source/resources/api/blender_launcher_api.json").resolve()
    internal_stable_build_path = Path(f"source/resources/api/stable_builds_api_{get_platform().lower()}.json").resolve()


def update_local_api_files(data):
    if not config_path.exists():
        config_path.mkdir(parents=True)
        logger.info(f"Created config directory in {config_path}")

    try:
        with open(bl_api_path, "w") as f:
            json.dump(data, f, indent=4)
            logger.info(f"Updated API file in {bl_api_path}")
        read_bl_api.cache_clear()
    except OSError as e:
        logger.error(f"Failed to write API file: {e}")


def update_stable_builds_cache(data):
    if not config_path.exists():
        config_path.mkdir(parents=True)
        logger.info(f"Created config directory in {config_path}")

    # If data no data from the API have been retrieve, read from the internal API file
    if data is None and internal_stable_build_path.is_file():
        try:
            with open(stable_build_path, "r") as f:
                data = json.load(f)
        except OSError as e:
            logger.error(f"Failed to write API file: {e}")
    if data is None:
        logger.error(f"Unable to retrieve online build API data and no internal API file found.")
        return
    if not stable_build_path.is_file():
        try:
            with open(stable_build_path, "w") as f:
                json.dump(data, f, indent=4)
                logger.info(f"Create Build Cache file in {stable_build_path}")
        except OSError as e:
            logger.error(f"Failed to write API file: {e}")
    else:
        try:
            with open(stable_build_path, "r") as f:
                current_data = json.load(f)
                current_data.update(data)
            with open(stable_build_path, "w") as f:
                json.dump(current_data, f, indent=4)
                logger.info(f"Updated Build Cache file in {stable_build_path}")
        except OSError as e:
            logger.error(f"Failed to write API file: {e}")


@lru_cache(maxsize=1)
def read_bl_api() -> dict:
    api = bl_api_path if bl_api_path.exists() else internal_bl_api_path
    if api == internal_bl_api_path:
        logger.error(f"API file not found in {bl_api_path}. Using internal API file.")

    with open(api) as f:
        return json.load(f)


def read_blender_version_list() -> dict[str, str]:
    return read_bl_api().get("blender_versions", {})


def lts_blender_version():
    return tuple(version for version, lts in read_blender_version_list().items() if lts == "LTS")


def dropdown_blender_version() -> dict[str, int]:
    """Ex:

    {
        "4.0": 0,
        "3.6": 1,
        "3.5": 2,
        "3.4": 3
    }
    """
    return {key: index for index, key in enumerate(read_blender_version_list().keys())}
