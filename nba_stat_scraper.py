from flask import Flask, jsonify
import pandas as pd
import requests


app = Flask(__name__)

pd.set_option('display.max_columns', None)

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Host': 'stats.nba.com',
    'Origin': 'https://www.nba.com',
    'Pragma': 'no-cache',
    'Referer': 'https://www.nba.com/',
    'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

@app.route('/scrape_stats', methods=['GET'])
def scrape_stats():
    try:
        season_types = ['Regular%20Season', 'Playoffs']
        years = ['2014-15', '2015-16', '2016-17', '2017-18', '2018-19', '2019-20', '2020-21', '2021-22', '2022-23', '2023-24']
        
        main_table = pd.DataFrame()

        for yr in years:
            for szn in season_types:
                api = f'https://stats.nba.com/stats/leagueLeaders?LeagueID=00&PerMode=Totals&Scope=S&Season={yr}&SeasonType={szn}&StatCategory=PTS'
                response = requests.get(url=api, headers=headers).json()
                temp_table = pd.DataFrame(response['resultSet']['rowSet'], columns=response['resultSet']['headers'])
                temp_table['Year'] = yr
                temp_table['Season_type'] = szn
                main_table = pd.concat([main_table, temp_table], ignore_index=True)
        
        return main_table.to_json(orient='records')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)