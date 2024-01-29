# Rare issues I have run into: 
# - this script will crash OBS if explorer.exe hangs 

import obspython as obs
import asyncio

# requires disabling the _winrt.init_apartment() in __init__.py
from winrt.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
# end of notes about pywinrt

interval = 15
source_name = ""


# ------------------------------------------------------------

def update_text():
    global interval
    global source_name

    source = obs.obs_get_source_by_name(source_name)
    current_media_info = asyncio.run(get_media_info())
    print(current_media_info)
    if source is not None and current_media_info is not None:
        settings = obs.obs_data_create()

        obs.obs_data_set_string(settings, "text",
                                str(f"{current_media_info['title'][:55]}\n{current_media_info['artist'][:35]}"))
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)

        obs.obs_source_release(source)
    else:
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", "No Media Playing")
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)

        obs.obs_source_release(source)


def refresh_pressed(props, prop):
    update_text()


# ------------------------------------------------------------

def script_description():
    return "Updates a text source to the current Media at every few seconds.\n\nBy slicedbread"


def script_update(settings):
    global interval
    global source_name

    interval = obs.obs_data_get_int(settings, "interval")
    source_name = obs.obs_data_get_string(settings, "source")

    obs.timer_remove(update_text)

    if source_name != "":
        obs.timer_add(update_text, interval * 1000)


def script_defaults(settings):
    obs.obs_data_set_default_int(settings, "interval", 15)


def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_int(props, "interval", "Update Interval (seconds)", 15, 90, 1)

    p = obs.obs_properties_add_list(props, "source", "Text Source", obs.OBS_COMBO_TYPE_EDITABLE,
                                    obs.OBS_COMBO_FORMAT_STRING)
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if source_id == "text_gdiplus" or source_id == "text_ft2_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p, name, name)

        obs.source_list_release(sources)

    obs.obs_properties_add_button(props, "button", "Refresh", refresh_pressed)
    return props


async def get_media_info():
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()
    try:
        if current_session is not None:
            info = await current_session.try_get_media_properties_async()
            info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info) if song_attr[0] != '_'}

            info_dict['genres'] = list(info_dict['genres'])

            return info_dict
    except:
        raise Exception('TARGET_PROGRAM is not the current media session')
