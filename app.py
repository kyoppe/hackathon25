import os
import re
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def extract_user_id(text):
    """Extract user ID from Slack mention format <@USER_ID>"""
    match = re.search(r'<@([A-Z0-9]+)>', text)
    return match.group(1) if match else None

@app.route('/slack/events', methods=['POST'])
def slack_events():
    # Get the JSON data from the request
    data = request.get_json()
    
    # Handle URL verification
    if data.get('type') == 'url_verification':
        return jsonify({'challenge': data['challenge']})
    
    # Handle app_mention and message events
    event = data.get('event', {})
    event_type = event.get('type')
    
    if event_type in ['app_mention', 'message']:
        text = event.get('text', '')
        giver = event.get('user')
        
        # Check for +g pattern
        if '+g' in text.lower():
            receiver = extract_user_id(text)
            if receiver:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f'[{timestamp}] Giver {giver} → Receiver {receiver} に +g')
    
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 