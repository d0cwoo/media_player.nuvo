"""Support for interfacing with Nuvo Multi-Zone Amplifier via serial/RS-232. """
# Modified from Monoprice core integration
# commented lines are not in the Monoprice core integration

import logging

# import voluptuous as vol

from serial import SerialException
from pynuvo import get_async_nuvo

from homeassistant import core
# from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)
# from homeassistant.components.media_player.const import (
#     DOMAIN,
#     SUPPORT_SELECT_SOURCE,
#     SUPPORT_TURN_OFF,
#     SUPPORT_TURN_ON,
#     SUPPORT_VOLUME_MUTE,
#     SUPPORT_VOLUME_SET,
#     SUPPORT_VOLUME_STEP,
# )
from homeassistant.const import (
    CONF_PORT, 
    STATE_OFF, 
    STATE_ON,
)
# from homeassistant.const import (
#     ATTR_ENTITY_ID, 
#     CONF_NAME,
#     CONF_PORT, 
#     CONF_TYPE,
#     STATE_OFF, 
#     STATE_ON,
# )
from homeassistant.helpers import config_validation as cv, entity_platform, service
# from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_SOURCES,
    DOMAIN,
    FIRST_RUN,
    NUVO_OBJECT,
    SERVICE_RESTORE,
    SERVICE_SNAPSHOT,
)

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1

SUPPORT_NUVO = (
    SUPPORT_VOLUME_MUTE 
    | SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_STEP
    | SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
    | SUPPORT_SELECT_SOURCE
)

MEDIA_PLAYER_SCHEMA = vol.Schema({ATTR_ENTITY_ID: cv.comp_entity_ids})

ZONE_SCHEMA = vol.Schema({vol.Required(CONF_NAME): cv.string})

SOURCE_SCHEMA = vol.Schema({vol.Required(CONF_NAME): cv.string})

CONF_ZONES = "zones"
CONF_SOURCES = "sources"
CONF_MODEL = "essentia"
DATA_NUVO = "nuvo"
ATTR_SOURCE = "source"
SERVICE_SNAPSHOT = 'snapshot'
SERVICE_RESTORE = 'restore'
SERVICE_SETALLZONES = "set_all_zones"

NUVO_SETALLZONES_SCHEMA = MEDIA_PLAYER_SCHEMA.extend(
    {vol.Required(ATTR_SOURCE): cv.string}
)

# Valid zone ids: 1-6
ZONE_IDS = vol.All(vol.Coerce(int), vol.Range(min=1, max=6))

# Valid source ids: 1-4
SOURCE_IDS = vol.All(vol.Coerce(int), vol.Range(min=1, max=4))

PLATFORM_SCHEMA = vol.All(
    cv.has_at_least_one_key(CONF_PORT),
    PLATFORM_SCHEMA.extend(
        {
            vol.Exclusive(CONF_PORT, CONF_TYPE): cv.string,
            vol.Required(CONF_ZONES): vol.Schema({ZONE_IDS: ZONE_SCHEMA}),
            vol.Required(CONF_SOURCES): vol.Schema({SOURCE_IDS: SOURCE_SCHEMA}),
            vol.Optional(CONF_MODEL): cv.string,
        }
    ),
)

# def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Nuvo platform."""
    if DATA_NUVO not in hass.data:
        hass.data[DATA_NUVO] = {}

    port = config.get(CONF_PORT)

    connection = None
    if port is not None:
        try:
            nuvo = get_nuvo(port)
            connection = port
        except SerialException:
            _LOGGER.error("Error connecting to the Nuvo controller via Serial")
            return

    sources = {
        source_id: extra[CONF_NAME] for source_id, extra in config[CONF_SOURCES].items()
    }

    devices = []
    for zone_id, extra in config[CONF_ZONES].items():
        _LOGGER.info("Adding zone %d - %s", zone_id, extra[CONF_NAME])
        unique_id = f"{connection}-{extra[CONF_NAME]}"  # change to entity ID.zone name
        _LOGGER.info("The unique_id is %s", unique_id)
        device = NuvoZone(nuvo, sources, zone_id, extra[CONF_NAME], unique_id)
        hass.data[DATA_NUVO][unique_id] = device
        devices.append(device)

    add_entities(devices, True)

    def service_handle(service):
        """Handle for services."""
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        source = service.data.get(ATTR_SOURCE)
        if entity_ids:
            devices = [
                device
                for device in hass.data[DATA_NUVO].values()
                if device.entity_id in entity_ids
            ]

        else:
            devices = hass.data[DATA_NUVO].values()

        for device in devices:
            if service.service == SERVICE_SETALLZONES:
                device.set_all_zones(source)

    hass.services.register(
        DOMAIN, SERVICE_SETALLZONES, service_handle, schema=NUVO_SETALLZONES_SCHEMA
    )

@core.callback
def _get_sources_from_dict(data):
    sources_config = data[CONF_SOURCES]

    source_id_name = {int(index): name for index, name in sources_config.items()}

    source_name_id = {v: k for k, v in source_id_name.items()}

    source_names = sorted(source_name_id.keys(), key=lambda v: source_name_id[v])

    return [source_id_name, source_name_id, source_names]


@core.callback
def _get_sources(config_entry):
    if CONF_SOURCES in config_entry.options:
        data = config_entry.options
    else:
        data = config_entry.data
    return _get_sources_from_dict(data)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """ Async setup for the Nuvo 6-zone amplifier platform. Modified from Monoprice core integration."""
    port = config_entry.data[CONF_PORT]

    nuvo = hass.data[DOMAIN][config_entry.entry_id][NUVO_OBJECT]

    sources = _get_sources(config_entry)

    entities = []
    for i in range (1, 4):
        for j in range (1, 7):
            zone_id = (i * 10) + j
            _LOGGER.info("Async: adding zone %d for port %s", zone_id, port)
            entities.append(
                NuvoZone(nuvo, sources, zone_id, config_entry.entry_id)
            )
    
    # only call update before add if it's the first run so we can try to detect zones
    first_run = hass.data[DOMAIN][config_entry.entry_id][FIRST_RUN]
    async_add_entities(entities, first_run)

    platform = entity_platform.current_platform.get()

    def _call_service(entities, service_call):
        for entity in entities:
            if service_call.service == SERVICE_SNAPSHOT:
                entity.snapshot()
            elif service_call.service == SERVICE_RESTORE:
                entity.restore()

    @service.verify_domain_control(hass, DOMAIN)
    async def async_service_handle(service_call):
        """Handle for services."""
        entities = await platform.async_extract_from_service(service_call)

        if not entities:
            return

        hass.async_add_executor_job(_call_service, entities, service_call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SNAPSHOT,
        async_service_handle,
        schema=cv.make_entity_service_schema({}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESTORE,
        async_service_handle,
        schema=cv.make_entity_service_schema({}),
    )

class NuvoZone(MediaPlayerEntity):
    """Representation of a Nuvo amplifier zone."""

    def __init__(self, nuvo, sources, zone_id, zone_name):
        """Initialize new zone."""
        self._nuvo = nuvo
        # dict source_id -> source name
        self._source_id_name = sources
        # dict source name -> source_id
        self._source_name_id = {v: k for k, v in sources.items()}
        # ordered list of all source names
        self._source_names = sorted(self._source_name_id.keys(),
                                    key=lambda v: self._source_name_id[v])
        self._zone_id = zone_id
        self._name = zone_name
        self._unique_id = f"{zone_name}_{self._zone_id}"
        # self._unique_id = unique_id  
        self._snapshot = None
        self._state = None
        self._volume = None
        self._source = None
        self._mute = None

    def update(self):
        """Retrieve latest state."""
        state = self._nuvo.zone_status(self._zone_id)
        if not state:
            return False
        self._state = STATE_ON if state.power else STATE_OFF
        self._volume = state.volume
        self._mute = state.mute
        idx = state.source
        if idx in self._source_id_name:
            self._source = self._source_id_name[idx]
        else:
            self._source = None
        return True

    @property
    def device_info(self):
        """Return device info for this device."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Nuvo",
            "model": "Essentia",
        }

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the zone."""
        return self._name

    @property
    def state(self):
        """Return the state of the zone."""
        return self._state

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        if self._volume is None:
            return None
        return (79 - self._volume) / 79.0   # Nuvo with vol 0=Max and 79=Min

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._mute

    @property
    def supported_features(self):
        """Return flag of media commands that are supported."""
        return SUPPORT_NUVO

    @property
    def media_title(self):
        """Return the current source as medial title."""
        return self._source

    @property
    def source(self):
        """Return the current input source of the device."""
        return self._source

    @property
    def source_list(self):
        """List of available input sources."""
        return self._source_names

    def snapshot(self):
        """Save zone's current state."""
        self._snapshot = self._nuvo.zone_status(self._zone_id)

    def restore(self):
        """Restore saved state."""
        if self._snapshot:
            self._nuvo.restore_zone(self._snapshot)
            self.schedule_update_ha_state(True)

    def select_source(self, source):
        """Set input source."""
        if source not in self._source_name_id:
            return
        idx = self._source_name_id[source]
        self._nuvo.set_source(self._zone_id, idx)

    def turn_on(self):
        """Turn the media player on."""
        self._nuvo.set_power(self._zone_id, True)

    def turn_off(self):
        """Turn the media player off."""
        self._nuvo.set_power(self._zone_id, False)
        
    def mute_volume(self, mute):
        """Mute (true) or unmute (false) media player."""
        self._nuvo.set_mute(self._zone_id, mute)

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        self._nuvo.set_volume(self._zone_id, int( 79 - volume * 79 ))

    def volume_up(self):
        """Volume up the media player."""
        if self._volume is None:
            return
        self._nuvo.set_volume(self._zone_id, max (self._volume - 1, 0))  # Nuvo: 0=Max and 79=Min

    def volume_down(self):
        """Volume down media player."""
        if self._volume is None:
            return
        self._nuvo.set_volume(self._zone_id, min (self._volume + 1, 79)) # Nuvo: 0=Max and 79=Min
