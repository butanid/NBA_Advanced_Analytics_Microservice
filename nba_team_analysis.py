from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import numpy as np
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('team_search.html')

@app.route('/analyze_team_stats', methods=['POST'])
def analyze_team_stats():
    try:
        team_name = request.form['team']
        start_year = int(request.form['start_year'])
        end_year = int(request.form['end_year'])

        # Fetch data from scraping microservice
        response = requests.get('http://localhost:5001/scrape_stats', timeout=60)
        data = pd.read_json(response.text)
        
        # Data preprocessing
        data['Year'] = data['Year'].str[:4].astype(int)
        data['Season_type'].replace('Regular%20Season', 'Regular', inplace=True)
        data.drop(columns=['RANK', 'PLAYER_ID', 'TEAM_ID', 'GP', 'MIN', 'EFF'], inplace=True)

        def stat_mean_data(table, start_year, end_year):
            table = table[(table['Year'] >= start_year) & (table['Year'] <= end_year)]
            
            # Exclude 'Year' column from mean calculations
            numeric_cols = table.select_dtypes(include=[np.number]).columns.tolist()
            if 'Year' in numeric_cols:
                numeric_cols.remove('Year')
            
            means = table[numeric_cols].mean(numeric_only=True).round(2)
            
            # Convert percentages to the correct format
            if 'FG_PCT' in means:
                means['FG_PCT'] = round(means['FG_PCT'] * 100)
            if 'FG3_PCT' in means:
                means['FG3_PCT'] = round(means['FG3_PCT'] * 100)
            if 'FT_PCT' in means:
                means['FT_PCT'] = round(means['FT_PCT'] * 100)
                
            # Add '%' symbol to percentage values
            if 'FG_PCT' in means:
                means['FG_PCT'] = f"{means['FG_PCT']}%"
            if 'FG3_PCT' in means:
                means['FG3_PCT'] = f"{means['FG3_PCT']}%"
            if 'FT_PCT' in means:
                means['FT_PCT'] = f"{means['FT_PCT']}%"
            
            return means.to_dict()

        if team_name in data['TEAM'].unique():
            team_data = data[data['TEAM'] == team_name]
            team_mean = stat_mean_data(team_data, start_year, end_year)
            return render_template('team_search.html', team_name=team_name, start_year=start_year, end_year=end_year, team_mean=team_mean)
        else:
            return redirect(url_for('home'))
    except Exception as e:
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)