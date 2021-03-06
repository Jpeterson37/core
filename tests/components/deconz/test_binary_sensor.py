"""deCONZ binary sensor platform tests."""
from copy import deepcopy

from homeassistant.components import deconz
import homeassistant.components.binary_sensor as binary_sensor
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_VIBRATION,
)
from homeassistant.helpers.entity_registry import async_entries_for_config_entry
from homeassistant.setup import async_setup_component

from .test_gateway import DECONZ_WEB_REQUEST, setup_deconz_integration

SENSORS = {
    "1": {
        "id": "Presence sensor id",
        "name": "Presence sensor",
        "type": "ZHAPresence",
        "state": {"dark": False, "presence": False},
        "config": {"on": True, "reachable": True, "temperature": 10},
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    },
    "2": {
        "id": "Temperature sensor id",
        "name": "Temperature sensor",
        "type": "ZHATemperature",
        "state": {"temperature": False},
        "config": {},
        "uniqueid": "00:00:00:00:00:00:00:01-00",
    },
    "3": {
        "id": "CLIP presence sensor id",
        "name": "CLIP presence sensor",
        "type": "CLIPPresence",
        "state": {},
        "config": {},
        "uniqueid": "00:00:00:00:00:00:00:02-00",
    },
    "4": {
        "id": "Vibration sensor id",
        "name": "Vibration sensor",
        "type": "ZHAVibration",
        "state": {
            "orientation": [1, 2, 3],
            "tiltangle": 36,
            "vibration": True,
            "vibrationstrength": 10,
        },
        "config": {"on": True, "reachable": True, "temperature": 10},
        "uniqueid": "00:00:00:00:00:00:00:03-00",
    },
}


async def test_platform_manually_configured(hass):
    """Test that we do not discover anything or try to set up a gateway."""
    assert (
        await async_setup_component(
            hass, binary_sensor.DOMAIN, {"binary_sensor": {"platform": deconz.DOMAIN}}
        )
        is True
    )
    assert deconz.DOMAIN not in hass.data


async def test_no_binary_sensors(hass):
    """Test that no sensors in deconz results in no sensor entities."""
    gateway = await setup_deconz_integration(hass)
    assert len(gateway.deconz_ids) == 0
    assert len(hass.states.async_all()) == 0


async def test_binary_sensors(hass):
    """Test successful creation of binary sensor entities."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["sensors"] = deepcopy(SENSORS)
    gateway = await setup_deconz_integration(hass, get_state_response=data)
    assert "binary_sensor.presence_sensor" in gateway.deconz_ids
    assert "binary_sensor.temperature_sensor" not in gateway.deconz_ids
    assert "binary_sensor.clip_presence_sensor" not in gateway.deconz_ids
    assert "binary_sensor.vibration_sensor" in gateway.deconz_ids
    assert len(hass.states.async_all()) == 3

    presence_sensor = hass.states.get("binary_sensor.presence_sensor")
    assert presence_sensor.state == "off"
    assert presence_sensor.attributes["device_class"] == DEVICE_CLASS_MOTION

    temperature_sensor = hass.states.get("binary_sensor.temperature_sensor")
    assert temperature_sensor is None

    clip_presence_sensor = hass.states.get("binary_sensor.clip_presence_sensor")
    assert clip_presence_sensor is None

    vibration_sensor = hass.states.get("binary_sensor.vibration_sensor")
    assert vibration_sensor.state == "on"
    assert vibration_sensor.attributes["device_class"] == DEVICE_CLASS_VIBRATION

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "1",
        "state": {"presence": True},
    }
    gateway.api.event_handler(state_changed_event)
    await hass.async_block_till_done()

    presence_sensor = hass.states.get("binary_sensor.presence_sensor")
    assert presence_sensor.state == "on"

    await gateway.async_reset()

    assert len(hass.states.async_all()) == 0


async def test_allow_clip_sensor(hass):
    """Test that CLIP sensors can be allowed."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["sensors"] = deepcopy(SENSORS)
    gateway = await setup_deconz_integration(
        hass,
        options={deconz.gateway.CONF_ALLOW_CLIP_SENSOR: True},
        get_state_response=data,
    )
    assert "binary_sensor.presence_sensor" in gateway.deconz_ids
    assert "binary_sensor.temperature_sensor" not in gateway.deconz_ids
    assert "binary_sensor.clip_presence_sensor" in gateway.deconz_ids
    assert "binary_sensor.vibration_sensor" in gateway.deconz_ids
    assert len(hass.states.async_all()) == 4

    presence_sensor = hass.states.get("binary_sensor.presence_sensor")
    assert presence_sensor.state == "off"

    temperature_sensor = hass.states.get("binary_sensor.temperature_sensor")
    assert temperature_sensor is None

    clip_presence_sensor = hass.states.get("binary_sensor.clip_presence_sensor")
    assert clip_presence_sensor.state == "off"

    vibration_sensor = hass.states.get("binary_sensor.vibration_sensor")
    assert vibration_sensor.state == "on"

    hass.config_entries.async_update_entry(
        gateway.config_entry, options={deconz.gateway.CONF_ALLOW_CLIP_SENSOR: False}
    )
    await hass.async_block_till_done()

    assert "binary_sensor.presence_sensor" in gateway.deconz_ids
    assert "binary_sensor.temperature_sensor" not in gateway.deconz_ids
    assert "binary_sensor.clip_presence_sensor" not in gateway.deconz_ids
    assert "binary_sensor.vibration_sensor" in gateway.deconz_ids
    assert len(hass.states.async_all()) == 3

    hass.config_entries.async_update_entry(
        gateway.config_entry, options={deconz.gateway.CONF_ALLOW_CLIP_SENSOR: True}
    )
    await hass.async_block_till_done()

    assert "binary_sensor.presence_sensor" in gateway.deconz_ids
    assert "binary_sensor.temperature_sensor" not in gateway.deconz_ids
    assert "binary_sensor.clip_presence_sensor" in gateway.deconz_ids
    assert "binary_sensor.vibration_sensor" in gateway.deconz_ids
    assert len(hass.states.async_all()) == 4


async def test_add_new_binary_sensor(hass):
    """Test that adding a new binary sensor works."""
    gateway = await setup_deconz_integration(hass)
    assert len(gateway.deconz_ids) == 0

    state_added_event = {
        "t": "event",
        "e": "added",
        "r": "sensors",
        "id": "1",
        "sensor": deepcopy(SENSORS["1"]),
    }
    gateway.api.event_handler(state_added_event)
    await hass.async_block_till_done()

    assert "binary_sensor.presence_sensor" in gateway.deconz_ids

    presence_sensor = hass.states.get("binary_sensor.presence_sensor")
    assert presence_sensor.state == "off"


async def test_add_new_binary_sensor_ignored(hass):
    """Test that adding a new binary sensor is not allowed."""
    gateway = await setup_deconz_integration(
        hass,
        options={deconz.gateway.CONF_ALLOW_NEW_DEVICES: False},
    )
    assert len(hass.states.async_all()) == 0

    state_added_event = {
        "t": "event",
        "e": "added",
        "r": "sensors",
        "id": "1",
        "sensor": deepcopy(SENSORS["1"]),
    }
    gateway.api.event_handler(state_added_event)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0

    entity_registry = await hass.helpers.entity_registry.async_get_registry()
    assert (
        len(
            async_entries_for_config_entry(
                entity_registry, gateway.config_entry.entry_id
            )
        )
        == 0
    )
