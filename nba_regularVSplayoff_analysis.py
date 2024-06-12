from flask import Flask, request, jsonify, render_template
import pandas as pd
import requests
import io
import json
import plotly.graph_objects as go
import plotly.io as pio

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
    return render_template('regVSplayoff_search.html')

@app.route('/comparison', methods=['GET'])
def comparison():
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
        
    # Initializing season type variables
    regular_data = player_data[player_data['Season_type']=='Regular%20Season']
    if regular_data.empty:
        return jsonify({'error': 'No Regular Season data found'}), 404
    
    playoff_data = player_data[player_data['Season_type']=='Playoffs']
    if playoff_data.empty:
        return jsonify({'error': 'No Playoff data found'}), 404
    
    total_cols = ['MIN', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'PTS', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
    
    def preprocess_stats(stats):
        stats[total_cols] = stats[total_cols].apply(pd.to_numeric, errors='coerce')
        stats['POSS_est'] = stats['FGA'] - stats['OREB'] + stats['TOV'] + 0.44 * stats['FTA']
        stats['POSS_per_48'] = (stats['POSS_est'] / stats['MIN']) * 48 * 5
        stats['FG%'] = stats['FGM'] / stats['FGA']
        stats['3PT%'] = stats['FG3M'] / stats['FG3A']
        stats['FT%'] = stats['FTM'] / stats['FTA']
        stats['AST%'] = stats['AST'] / stats['FGM']
        stats['FG3A%'] = stats['FG3A'] / stats['FGA']
        stats['PTS/FGA'] = stats['PTS'] / stats['FGA']
        stats['FG3M/FGM'] = stats['FG3M'] / stats['FGM']
        stats['FTA/FGA'] = stats['FTA'] / stats['FGA']
        stats['TRU%'] = 0.5 * stats['PTS'] / (stats['FGA'] + 0.475 * stats['FTA'])
        stats['AST_TOV'] = stats['AST'] / stats['TOV']
        for col in total_cols:
            stats[col] = 100 * stats[col] / stats['POSS_est']
        stats.drop(columns=['MIN','POSS_est'], inplace=True)
        return stats

    regular_stats = preprocess_stats(regular_data.groupby(['PLAYER', 'PLAYER_ID', 'Year'])[total_cols].sum().reset_index())
    playoff_stats = preprocess_stats(playoff_data.groupby(['PLAYER', 'PLAYER_ID', 'Year'])[total_cols].sum().reset_index())

    comp_cols = ['FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'PTS', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'POSS_per_48', 'FG3M/FGM', 'FTA/FGA', 'TRU%', 'AST_TOV']    
    comp_szn = (playoff_stats.set_index(['PLAYER', 'PLAYER_ID', 'Year'])[comp_cols] - 
                regular_stats.set_index(['PLAYER', 'PLAYER_ID', 'Year'])[comp_cols]) / regular_stats.set_index(['PLAYER', 'PLAYER_ID', 'Year'])[comp_cols] * 100
    comp_szn = comp_szn.reset_index()
    comp_szn = comp_szn.melt(id_vars=['PLAYER', 'PLAYER_ID', 'Year'], var_name='Stat', value_name='Percentage Change')

    # Generate a plotly graph
    fig = go.Figure()
    for stat in comp_cols:
        fig.add_trace(go.Scatter(x=comp_szn[comp_szn['Stat'] == stat]['Year'],
                                 y=comp_szn[comp_szn['Stat'] == stat]['Percentage Change'],
                                 mode='lines+markers',
                                 name=stat))
    fig.update_layout(title=f'Regular Season vs Playoffs Stat Differential for {player}',
                      xaxis_title='Season',
                      yaxis_title='Percentage Change (%)')

    graph_html = pio.to_html(fig, full_html=False)

    return render_template('regVSplayoff_search.html', player=player, graph_html=graph_html)


if __name__ == '__main__':
    app.run(debug=True, port=5005)