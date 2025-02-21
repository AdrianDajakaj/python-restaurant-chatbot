import json
import os
import datetime
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

def load_opening_hours():
    file_path = os.path.join(os.path.dirname(__file__), "restaurant_data", "opening_hours.json")
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def load_menu():
    file_path = os.path.join(os.path.dirname(__file__), "restaurant_data", "menu.json")
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def load_order():
    file_path = os.path.join(os.path.dirname(__file__), "restaurant_data", "temporary_order.json")
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def save_order(data):
    file_path = os.path.join(os.path.dirname(__file__), "restaurant_data", "temporary_order.json")
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


DAYS_MAP = {
    "mon": "Monday", "monday": "Monday",
    "tue": "Tuesday", "tuesday": "Tuesday",
    "wed": "Wednesday", "wednesday": "Wednesday",
    "thu": "Thursday", "thursday": "Thursday",
    "fri": "Friday", "friday": "Friday",
    "sat": "Saturday", "saturday": "Saturday",
    "sun": "Sunday", "sunday": "Sunday",
}

class ActionCheckRestaurantOpen(Action):
    def name(self):
        return "action_check_restaurant_open"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        hours_data = load_opening_hours()

        day_text = next(tracker.get_latest_entity_values("day_of_week"), None)
        time_text = next(tracker.get_latest_entity_values("time"), None)

        today = datetime.datetime.today()
        days_relative = {
            "today": today.strftime("%A"),
            "yesterday": (today - datetime.timedelta(days=1)).strftime("%A"),
            "tomorrow": (today + datetime.timedelta(days=1)).strftime("%A"),
        }

        day_normalized = days_relative.get(day_text.lower(), DAYS_MAP.get(day_text.lower(), today.strftime("%A")))

        opening_hours = hours_data["items"].get(day_normalized, {"open": "?", "close": "?"})
        open_time, close_time = opening_hours["open"], opening_hours["close"]

        if open_time == "?" or close_time == "?":
            dispatcher.utter_message(text=f"I don't have information about the opening hours on {day_normalized}.")
            return []

        if not time_text:
            message = f"The restaurant is open on {day_normalized} from {open_time}:00 to {close_time}:00."
            dispatcher.utter_message(text=message)
            return [SlotSet("day_of_week", day_normalized)]

        try:
            parsed_time = datetime.datetime.strptime(time_text, "%H:%M") if ":" in time_text else datetime.datetime.strptime(time_text, "%I %p")
            current_time = parsed_time.hour
        except ValueError:
            dispatcher.utter_message(text="I don't understand the time you provided. Please use a format like 14:30 or 10 AM.")
            return []

        if open_time <= current_time < close_time:
            message = f"Yes, the restaurant is open on {day_normalized} at {current_time}:00."
        else:
            message = f"No, the restaurant is closed on {day_normalized} at {current_time}:00."

        dispatcher.utter_message(text=message)
        return [SlotSet("day_of_week", day_normalized)]


class ActionShowMenu(Action):
    def name(self):
        return "action_show_menu"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        menu_data = load_menu()

        menu_items = menu_data["items"]
        menu_message = "Here is our menu:\n"
        i = 1
        for item in menu_items:
            menu_message += f"{i}) {item['name']}: ${item['price']} \n"
            i+=1

        dispatcher.utter_message(text=menu_message)
        return []

class ActionOrderBegin(Action):
    def name(self):
        return "action_order_begin"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        dispatcher.utter_message(text="Of course. Now please select the dishes to order.")
        type_of_order = next(tracker.get_latest_entity_values("order_type"), None)
        if type_of_order:
            order_data = {
                "orderType": "",
                "orderPositions": [],
                "orderAddress": ""
            }
            order_data["orderType"] = type_of_order
            save_order(order_data)


class ActionCheckDishInMenu(Action):
    def name(self):
        return "action_check_dish_in_menu"
    
    def run(self, dispatcher, tracker, domain):
        dish = tracker.get_slot('dish')
        menu_data = load_menu()
        menu = menu_data["items"]
        
        dish_found = next((item for item in menu if item['name'].lower() == dish.lower()), None)
        
        if dish_found:
            dispatcher.utter_message(f"Great choice! The preparation time for {dish} is {dish_found['preparation_time']} hours.")
            order_data = load_order()
            new_position = {
                "name": dish_found["name"],
                "price": dish_found["price"],
                "preparation_time": dish_found['preparation_time'],
                "modifications": ""
            }
            order_data["orderPositions"].append(new_position)
            save_order(order_data)
            return [SlotSet('dish', dish)]
        else:
            dispatcher.utter_message(f"Sorry, we don't have {dish} on the menu.")
            return []

class ActionAdressProvider(Action):
    def name(self):
        return "action_adress_provider"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        address = next(tracker.get_latest_entity_values("address"), None)
        order_data = load_order()
        order_data["orderAddress"] = address
        save_order(order_data)

class ActionOrderSummarize(Action):
    def name(self):
        return "action_order_summarize"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        order_data = load_order() 
        order_type = order_data.get("orderType", "Not specified")
        order_address = order_data.get("orderAddress", "Not specified")
        order_summary = f"Your order type is: {order_type}.\n"
        
        if order_address:
            order_summary += f"Delivery address: {order_address}.\n"
        
        order_summary += "\nYour order includes the following items:\n"

        order_items = order_data["orderPositions"]
        i = 1
        for item in order_items:
            order_summary += f"{i}) {item['name']}: ${item['price']} \n"
            i+=1

        dispatcher.utter_message(text=order_summary)

        return []





