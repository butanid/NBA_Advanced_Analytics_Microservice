from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

MICROSERVICES = {
    'team_analysis': 'http://127.0.0.1:5002/',
    'player_analysis': 'http://127.0.0.1:5003/',
    'stat_correlation': 'http://127.0.0.1:5004/',
    'regular_vs_playoff': 'http://127.0.0.1:5005/',
    'image_generator': 'http://127.0.0.1:5007/',
}

@app.route('/')
def home():
    return render_template('index.html', services=MICROSERVICES)

@app.route('/<service>')
def redirect_to_service(service):
    if service in MICROSERVICES:
        return redirect(MICROSERVICES[service])
    return "Service not found", 404

if __name__ == '__main__':
    app.run(port=5008, debug=True)