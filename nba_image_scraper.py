from io import BytesIO
from flask import Flask
from flask import send_file
import requests
from nba_api.stats.static import teams
from nba_api.stats.static import players

app = Flask(__name__)

@app.route('/get_team_logo/<team_abbreviation>')

def get_team_logo(team_abbreviation):
    team = teams.find_team_by_abbreviation(team_abbreviation)
    if team is None:
        return 'Team not found', 404
    team_id = team['id']
    return requests.get(f'https://cdn.nba.com/logos/nba/{team_id}/primary/L/logo.svg').content

@app.route('/get_player_headshot/<player_name>')

def get_player_headshot(player_name):
    player = players.find_players_by_full_name(player_name)
    if player is None:
        return 'Player not found', 404
    elif len(player) > 1:
        return 'Multiple players found', 400
    player_id = player[0]['id']
    headshot = requests.get(f'https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png').content
    buffer = BytesIO()
    buffer.write(headshot)
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png')

if __name__ == '__main__':
    app.run(port=5006)
