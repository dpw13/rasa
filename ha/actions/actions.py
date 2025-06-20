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

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction, SlotSet

logger = logging.getLogger(__name__)

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

    # Docs: Concepts -> Actions -> Forms
    async def validate_amount(
        self, slot_value: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        # Convert NL "amount" slot into absolute/relative and a float
        logger.info(f"Found amount '{slot_value}'")
        if slot_value in self.AMOUNT_TO_VAL:
            t = self.AMOUNT_TO_VAL[slot_value]
            return {"amount": slot_value, "amount_type": t[0], "amount_val": t[1]}

        return {"amount": slot_value}