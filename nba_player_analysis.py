from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import numpy as np
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('player_search.html')

@app.route('/analyze_player_stats', methods=['POST'])
def analyze_player_stats():
    try:
        player_name = request.form['player']
        start_year = int(request.form['start_year'])
        end_year = int(request.form['end_year'])

        # Fetch data from scraping microservice
        response = requests.get('http://localhost:5001/scrape_stats', timeout=60)
        data = pd.read_json(response.text)

        print(data.head())
        
        # Data preprocessing
        data['Year'] = data['Year'].str[:4].astype(int)
        data['Season_type'].replace('Regular%20Season', 'Regular', inplace=True)
        data.drop(columns=['RANK', 'PLAYER_ID', 'TEAM_ID', 'GP', 'MIN', 'EFF'], inplace=True)

        def player_stat_data(table, start_year, end_year):
            table = table[(table['Year'] >= start_year) & (table['Year'] <= end_year)]

            # Exclude 'Year' column from mean calculations
            numeric_cols = table.select_dtypes(include=[np.number]).columns.tolist()
            if 'Year' in numeric_cols:
                numeric_cols.remove('Year')
            
            player_means = table[numeric_cols].mean(numeric_only=True).round(2)
            
            # Convert percentages to the correct format
            if 'FG_PCT' in player_means:
                player_means['FG_PCT'] = round(player_means['FG_PCT'] * 100)
            if 'FG3_PCT' in player_means:
                player_means['FG3_PCT'] = round(player_means['FG3_PCT'] * 100)
            if 'FT_PCT' in player_means:
                player_means['FT_PCT'] = round(player_means['FT_PCT'] * 100)
                
            # Add '%' symbol to percentage values
            if 'FG_PCT' in player_means:
                player_means['FG_PCT'] = f"{player_means['FG_PCT']}%"
            if 'FG3_PCT' in player_means:
                player_means['FG3_PCT'] = f"{player_means['FG3_PCT']}%"
            if 'FT_PCT' in player_means:
                player_means['FT_PCT'] = f"{player_means['FT_PCT']}%"
            
            return player_means.to_dict()

        if player_name in data['PLAYER'].unique():
            player_data = data[data['PLAYER'] == player_name]
            player_mean = player_stat_data(player_data, start_year, end_year)
            return render_template('player_search.html', player_name=player_name, start_year=start_year, end_year=end_year, player_mean=player_mean)
        else:
            return redirect(url_for('home'))
    except Exception as e:
        return f"An error occurred: {e}", 500

    
if __name__ == '__main__':
    app.run(debug=True, port=5003)