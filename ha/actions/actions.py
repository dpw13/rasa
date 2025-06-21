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
from rasa_sdk.events import BotUttered, SlotSet
from rasa_sdk.forms import FormValidationAction

logger = logging.getLogger(__name__)


TEST_DEVICE_LIST = {
    "basement": {
        "light": 4,
        "fan": 1,
    },
    "upstairs": {
        "light": 2,
    },
    "living room": {
        "fan": 1,
        "light": 4,
    },
}


class ValidateAdjustForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_adjust_form"

    # Format: dict{txt: (Absolute, Amount)}
    AMOUNT_TO_VAL = {
        "up": ("relative", 0.20),
        "down": ("relative", 0.20),
        "on": ("absolute", 1.0),
        "off": ("absolute", 0.0),
    }

    async def validate_location(
        self, slot_value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        if slot_value not in TEST_DEVICE_LIST:
            dispatcher.utter_message(f"Sorry, I don't know the location {slot_value}")
            return {"location": None}
        else:
            return {"location": slot_value}

    # TODO: validate device to try to find a set of devices given the other constraints
    def validate_device(
        self, slot_value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        # TODO: better lemmatization
        slot_value = slot_value.rstrip("s")
        location = tracker.slots["location"]
        for loc, devices in TEST_DEVICE_LIST.items():
            if location is None or loc == location:
                if slot_value in devices:
                    return {"device": slot_value}

        if location is None:
            # TODO: this doesn't work. How do we emit messages back to the user? Set an error or warning slot?
            logger.warning(f"no device '{slot_value}' found")
            dispatcher.utter_message(f"Sorry, I don't know of any devices called {slot_value}")
        else:
            logger.warning(f"no device '{slot_value}' found for {location}")
            dispatcher.utter_message(f"Sorry, I don't know of any devices called {slot_value} in {location}")
        return {"device": None}

    # TODO: indicate how many devices were altered when form is submitted

    # Docs: Concepts -> Actions -> Forms
    def validate_amount(
        self, slot_value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        # Convert NL "amount" slot into absolute/relative and a float
        logger.info(f"Found amount '{slot_value}'")
        if slot_value in self.AMOUNT_TO_VAL:
            t = self.AMOUNT_TO_VAL[slot_value]
            return {"amount": slot_value, "amount_type": t[0], "amount_val": t[1]}

        return {"amount": slot_value}

class SubmitAdjust(Action):

    def name(self) -> Text:

        return "action_submit_adjust"

    async def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        args = {k: tracker.slots[k] for k in ["location", "device", "amount_type", "amount_val"]}
        logger.info(f"Executing: {args}")
        return []