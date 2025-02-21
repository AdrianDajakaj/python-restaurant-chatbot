import requests
from flask import Flask, request
from pymessenger.bot import Bot

# Twoje dane
ACCESS_TOKEN = "EAAhAHoI2pScBOZB8MXFQ6JJjnHy3P2dpCnuljdzWlZCRdIsZB3XBPZCs19VTAGatpLC0NZCxAiAXRdRfy4pKQlCZBuyP1UjflG5kdnoZA6uTsZBufgSaqkTs5X66PDHfowlEZCiu1NfaO1MBn4mlfE8w9Y7TEwpD5pbyzMCQPZBmqqsaNwKYb1ftNq9rt71LOfITN58gkEo6zeOhcyi7fmxQZDZD"
VERIFY_TOKEN = '2tKRxUYXnt9cvII5aFtt0AIkAZa_3B5zjkcMWQsGPn8gSNqBD'

# Konfiguracja aplikacji Flask
app = Flask(__name__)
bot = Bot(ACCESS_TOKEN)

# Endpoint do odbierania wiadomości
@app.route("/", methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    else:
        output = request.get_json()
        for event in output['entry']:            
            if 'messaging' in event:
                messaging = event['messaging']
                for message in messaging:
                    if message.get('message'):
                        recipient_id = message['sender']['id']
                        if message['message'].get('text'):
                            user_message = message['message'].get('text')
                            response_sent_text = get_message_from_rasa(user_message)  # Pobieranie odpowiedzi z Rasa
                            send_message(recipient_id, response_sent_text)
                return "Message Processed"

# Funkcja do weryfikacji webhooka
def verify_fb_token(token_sent):
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

def get_message_from_rasa(user_message):
    rasa_url = "http://localhost:5005/webhooks/rest/webhook" 
    payload = {
        "message": user_message
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(rasa_url, json=payload, headers=headers)
    response_data = response.json()

    if response_data:
        return response_data[0].get("text", "Sorry, I didn't understand that.")
    else:
        return "Sorry, I didn't understand that."

def send_message(recipient_id, response):
    bot.send_text_message(recipient_id, response)
    return "success"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
