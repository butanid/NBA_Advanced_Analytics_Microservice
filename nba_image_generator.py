from flask import Flask, request, render_template, send_file, jsonify
import requests
from io import BytesIO

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('image_generator.html')

@app.route('/generate_image', methods=['POST'])
def generate_image():
    team_abbreviation = request.form.get('team_abbreviation')
    player_name = request.form.get('player_name')
    try:
        if team_abbreviation:
            response = requests.get(f'http://localhost:5006/get_team_logo/{team_abbreviation}')
            if response.status_code == 200:
                return send_file(BytesIO(response.content), mimetype='image/svg+xml', download_name=f'{team_abbreviation}.svg')
            else:
                return f'Failed to retrieve team logo: {response.text}', response.status_code
        elif player_name:
            response = requests.get(f'http://localhost:5006/get_player_headshot/{player_name}')
            if response.status_code == 200:
                return send_file(BytesIO(response.content), mimetype='image/png', download_name=f'{player_name}.png')
            else:
                return f'Failed to retrieve player headshot: {response.text}', response.status_code
        return 'No input provided', 400
    except Exception as e:
        app.logger.error(f'Error generating image: {e}')
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(port=5007, debug=True)