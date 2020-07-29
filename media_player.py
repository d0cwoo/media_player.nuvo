import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

# Import the device class from the component that you want to support
from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
from homeassistant.components.media_player.const import (
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_STEP,
    SUPPORT_VOLUME_SET,
)

from homeassistant.const import ATTR_ENTITY_ID, CONF_HOST, CONF_NAME, CONF_PORT, STATE_OFF, STATE_ON

_LOGGER = logging.getLogger(__name__)

SUPPORT_NUVO = (
                 SUPPORT_SELECT_SOURCE
               | SUPPORT_VOLUME_MUTE
               | SUPPORT_VOLUME_SET
               | SUPPORT_VOLUME_STEP
               | SUPPORT_TURN_ON
               | SUPPORT_TURN_OFF
)

ZONE_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
})

SOURCE_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
})

CONF_ZONES = 'zones'
CONF_SOURCES = 'sources'
CONF_MODEL = 'model'

DATA_NUVO = 'nuvo'

SERVICE_SNAPSHOT = 'snapshot'
SERVICE_RESTORE = 'restore'

# Valid zone ids: 1-20
ZONE_IDS = vol.All(vol.Coerce(int), vol.Any(
    vol.Range(min=1, max=20)))

# Valid source ids: 1-6
SOURCE_IDS = vol.All(vol.Coerce(int), vol.Range(min=1, max=6))

MEDIA_PLAYER_SCHEMA = vol.Schema({ATTR_ENTITY_ID: cv.comp_entity_ids})

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PORT): cv.string,
    vol.Required(CONF_ZONES): vol.Schema({ZONE_IDS: ZONE_SCHEMA}),
    vol.Required(CONF_SOURCES): vol.Schema({SOURCE_IDS: SOURCE_SCHEMA}),
    vol.Optional(CONF_MODEL): cv.string,
})
