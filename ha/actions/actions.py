# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []

import logging
from typing import Dict, Text, List, Optional, Any

from rasa_sdk import Tracker, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType, BotUttered, SlotSet, AllSlotsReset
from rasa_sdk.forms import FormValidationAction

logger = logging.getLogger(__name__)


TEST_DEVICE_LIST = {
    "basement": {
        "light": {
            "brightness": 4,
        },
        "fan": {
            "speed": 1,
        },
        "thermostat": {
            "temperature": 72,
        },
    },
    "upstairs": {
        "light": {
            "brightness": 2,
        },
    },
    "living room": {
        "fan": {
            "speed": 1,
        },
        "light": {
            "brightness": 4,
        },
        "thermostat": {
            "temperature": 72,
        },
    },
}


class DeviceLocationForm(FormValidationAction):

    def name(self) -> Text:
        return "_helper_device_location_form"

    async def validate_location(
        self, slot_value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        if slot_value not in TEST_DEVICE_LIST:
            dispatcher.utter_message(f"Sorry, I don't know the location {slot_value}")
            return {"location": None}
        else:
            return {"location": slot_value}

    def validate_device(
        self, slot_value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        """Validate device to try to find a set of devices given the other constraints."""
        # TODO: better lemmatization
        # TODO: determine whether we allow multiple matches by whether the device is plural
        # TODO: support multiple matching devices
        slot_value = slot_value.rstrip("s")
        location = tracker.slots["location"]
        for loc, devices in TEST_DEVICE_LIST.items():
            if location is None or loc == location:
                if slot_value in devices:
                    logger.debug("Found matching device %s %s", loc, slot_value)
                    parameters = list(devices[slot_value].keys())
                    return {"device": slot_value, "parameter": parameters[0]}

        if location is None:
            logger.warning(f"no device '{slot_value}' found")
            dispatcher.utter_message(f"Sorry, I don't know of any devices called {slot_value}")
        else:
            logger.warning(f"no device '{slot_value}' found for {location}")
            dispatcher.utter_message(f"Sorry, I don't know of any devices called {slot_value} in {location}")
        return {"device": None}

    def validate_parameter(
        self, slot_value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        """Validate parameter to try to find a set of devices given the other constraints."""

        # TODO: support multiple matching devices
        location = tracker.slots["location"]
        for loc, devices in TEST_DEVICE_LIST.items():
            if location is None or loc == location:
                for device, params in devices.items():
                    if slot_value in params:
                        logger.debug("Found matching device %s %s with parameter %s", loc, device, slot_value)
                        return {"device": device, "parameter": slot_value}

        # No matching device was found. At this point just determine how we want to respond to
        # the user.
        if location is None:
            logger.warning(f"no devices with '{slot_value}' found")
            dispatcher.utter_message(f"Sorry, I don't know of any devices with a {slot_value}")
        else:
            logger.warning(f"no devices with '{slot_value}' found for {location}")
            dispatcher.utter_message(f"Sorry, I don't know of any devices with a {slot_value} in {location}")
        return {"parameter": None}


class DeviceAmountForm(DeviceLocationForm):
    """Common functions for validating and parsing amounts."""

    def name(self) -> Text:
        return "_helper_device_amount_form"

    # Format: dict{txt: (Absolute, Amount)}
    AMOUNT_TO_VAL = {
        "up": ("relative", 0.20),
        "down": ("relative", 0.20),
        "on": ("absolute", 1.0),
        "off": ("absolute", 0.0),
    }

    # Docs: Concepts -> Actions -> Forms
    def validate_amount(
        self, slot_value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        # Convert NL "amount" slot into absolute/relative and a float
        logger.info(f"Found amount '{slot_value}'")
        if slot_value in self.AMOUNT_TO_VAL:
            t = self.AMOUNT_TO_VAL[slot_value]
            return {"amount": slot_value, "amount_type": t[0], "amount_val": t[1]}

        words = slot_value.split(" ")
        mult = 1
        ret = {"amount": slot_value}
        for word in words:
            if word == "percent":
                mult = 0.01
            else:
                try:
                    ret["amount_val"] = float(word)
                    ret["amount_type"] = "absolute"
                except:
                    pass

        if "amount_val" in ret:
            # Apply percentage or units
            ret["amount_val"] *= mult

        return ret


class ValidateAdjustForm(DeviceAmountForm):
    def name(self) -> Text:
        return "validate_adjust_form"

class SubmitAdjust(Action):
    """Action for submitting a change to a device."""

    def name(self) -> Text:
        return "action_submit_adjust"

    # TODO: indicate how many devices were altered when form is submitted
    async def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """Apply the requested adjustment and report back."""
        args = {k: tracker.slots[k] for k in ["location", "device", "parameter", "amount_type", "amount_val"]}
        logger.info(f"Executing: {args}")

        try:
            loc = TEST_DEVICE_LIST[tracker.slots["location"]]
            dev = loc[tracker.slots["device"]]
            dev[tracker.slots["parameter"]] = tracker.slots["amount_val"]
            # TODO: May be better to set a slot and utter something in domain.yml
            # TODO: support multiple devices being set at once
            dispatcher.utter_message(f"Set {tracker.slots['device']} {tracker.slots['parameter']} to {tracker.slots['amount_val']}")
        except KeyError as e:
            logger.exception(e)
            dispatcher.utter_message(f"Sorry, there was an error setting the {tracker.slots['device']} {tracker.slots['parameter']}.")

        return [AllSlotsReset()]

########################
# Queries
########################


class ValidateQueryForm(DeviceLocationForm):
    def name(self) -> Text:
        return "validate_query_parameter_form"

class SubmitQuery(Action):
    """Action for submitting a change to a device."""

    def name(self) -> Text:
        return "action_submit_query_parameter"

    async def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any],
    ) -> List[EventType]:
        args = {k: tracker.slots[k] for k in ["location", "device", "parameter"]}
        logger.info(f"Executing: {args}")

        try:
            loc = TEST_DEVICE_LIST[tracker.slots["location"]]
            dev = loc[tracker.slots["device"]]
            amount = dev[tracker.slots["parameter"]]
            # TODO: May be better to set a slot and utter something in domain.yml
            dispatcher.utter_message(f"The {tracker.slots['location']} {tracker.slots['device']} {tracker.slots['parameter']} is {amount}")
        except KeyError as e:
            logger.exception(e)
            dispatcher.utter_message(f"Sorry, there was an error getting the {tracker.slots['device']} {tracker.slots['parameter']}.")

        return [AllSlotsReset()]

class SubmitFilter(Action):
    def name(self) -> Text:
        return "action_submit_filter"

    async def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        logger.warning("UNIMPLEMENTED")
        return [AllSlotsReset()]