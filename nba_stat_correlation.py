from flask import Flask, request, jsonify, render_template
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import json

app = Flask(__name__)

SCRAPER_URL = "http://localhost:5001/scrape_stats"

def get_stats_data():
    try:
        response = requests.get(SCRAPER_URL)
        response.raise_for_status()
        data = response.json()
        json_str = json.dumps(data)
        return pd.read_json(io.StringIO(json_str), orient='records'), None
    except requests.exceptions.RequestException as e:
        return None, str(e)

@app.route('/')
def home():
    return render_template('stat_correlation.html')

@app.route('/correlation', methods=['GET'])
def correlation():
    player = request.args.get('player')
    start_year = request.args.get('start_year')
    end_year = request.args.get('end_year')

    if not player:
        return jsonify({'error': 'Player name is required'}), 400
    
    data, error = get_stats_data()
    if error:
        return jsonify({'error': error}), 500

    player_data = data[data['PLAYER'] == player]
    if player_data.empty:
        return jsonify({'error': 'Player not found'}), 404

    # Filter by year range
    if start_year and end_year:
        player_data = player_data[(player_data['Year'] >= start_year) & (player_data['Year'] <= end_year)]
        if player_data.empty:
            return jsonify({'error': 'No data available for the specified year range'}), 404

    # Calculate per-minute statistics
    total_cols = ['MIN', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'PTS', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
    data_per_min = player_data.groupby(['PLAYER', 'PLAYER_ID', 'Year'])[total_cols].sum().reset_index()
    for col in total_cols[1:]:
        data_per_min[col] = data_per_min[col] / data_per_min['MIN']
    
    data_per_min['FG%'] = data_per_min['FGM'] / data_per_min['FGA']
    data_per_min['3PT%'] = data_per_min['FG3M'] / data_per_min['FG3A']
    data_per_min['FT%'] = data_per_min['FTM'] / data_per_min['FTA']
    data_per_min['FG3A%'] = data_per_min['FG3A'] / data_per_min['FGA']
    data_per_min['PTS/FGA'] = data_per_min['PTS'] / data_per_min['FGA']
    data_per_min['FG3M/FGM'] = data_per_min['FG3M'] / data_per_min['FGM']
    data_per_min['FTA/FGA'] = data_per_min['FTA'] / data_per_min['FGA']
    data_per_min['TRU%'] = 0.5 * data_per_min['PTS'] / (data_per_min['FGA'] + 0.475 * data_per_min['FTA'])
    data_per_min['AST_TOV'] = data_per_min['AST'] / data_per_min['TOV']
    
    # Minimum minutes played filter
    data_per_min = data_per_min[data_per_min['MIN'] >= 50]
    data_per_min.drop(columns='PLAYER_ID', inplace=True)

    # Select only the numerical columns
    numerical_data = data_per_min.select_dtypes(include=[float, int])

    if numerical_data.empty:
        return jsonify({'error': 'No numerical data available for correlation'}), 404
    
    corr = numerical_data.corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=False, fmt='.2f', cmap='coolwarm')
    plt.title(f'Stat Correlation for {player}')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_png = buf.getvalue()
    buf.close()
    encoded_image = base64.b64encode(image_png).decode('utf-8')
    
    return jsonify({'image': encoded_image})

if __name__ == '__main__':
    app.run(debug=True, port=5004)