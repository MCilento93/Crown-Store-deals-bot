# webapp site: https://crown-store-deals-bot--mariocilento93.repl.co/

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "<b>Web app for the discord bot 'Crown Store deals'</b>"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()