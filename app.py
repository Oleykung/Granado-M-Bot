from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
import json, datetime, os

BASE = Path(__file__).parent
BOSSES_FILE = BASE / "bosses.json"
TIMERS_FILE = BASE / "timers.json"

app = Flask(__name__)

def load_bosses():
    try:
        with open(BOSSES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def load_timers():
    try:
        with open(TIMERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_timers(data):
    with open(TIMERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_bosses(bosses):
    with open(BOSSES_FILE, "w", encoding="utf-8") as f:
        json.dump(bosses, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    try:
        return send_from_directory(str(BASE), "index.html")
    except:
        return "<h1>Granado Espada M Boss Tracker - Deploy OK</h1>"

@app.route("/api/bosses")
def api_bosses():
    return jsonify(load_bosses())

@app.route("/api/timers")
def api_timers():
    return jsonify(load_timers())

@app.route("/api/ping")
def api_ping():
    return jsonify({"status":"alive","uptime":"24h"})

@app.route("/api/status")
def api_status():
    return jsonify({"status":"ok","bosses":len(load_bosses()),"timers":len(load_timers()),"mode":"Flask WSGI Fixed"})

@app.route("/api/bosses", methods=["POST"])
def api_add_boss():
    data=request.get_json()
    bosses=load_bosses()
    if any(b["id"]==data["id"] for b in bosses):
        return jsonify({"error":"id exists"}),400
    bosses.append(data)
    save_bosses(bosses)
    return jsonify({"ok":True})

@app.route("/api/bosses/<bid>", methods=["PUT"])
def api_update_boss(bid):
    data=request.get_json()
    bosses=load_bosses()
    for i,b in enumerate(bosses):
        if b["id"]==bid:
            data["id"]=bid
            bosses[i]=data
            save_bosses(bosses)
            return jsonify({"ok":True})
    return jsonify({"error":"not found"}),404

@app.route("/api/bosses/<bid>", methods=["DELETE"])
def api_delete_boss(bid):
    bosses=load_bosses()
    new_list=[b for b in bosses if b["id"]!=bid]
    if len(new_list)==len(bosses):
        return jsonify({"error":"not found"}),404
    save_bosses(new_list)
    timers=load_timers()
    timers.pop(bid,None)
    save_timers(timers)
    return jsonify({"ok":True})

@app.route("/api/kill", methods=["POST"])
def api_kill():
    data=request.get_json()
    bid=data.get("id")
    bosses=load_bosses()
    boss=next((b for b in bosses if b["id"]==bid),None)
    if not boss:
        return jsonify({"error":"boss not found"}),404
    now=datetime.datetime.now()
    next_spawn=now+datetime.timedelta(minutes=boss.get("respawn_min",60))
    timers=load_timers()
    timers[bid]={"last_killed":now.isoformat(),"next_spawn":next_spawn.isoformat(),"killed_by":"web-render","notified_10m":False,"notified_spawn":False}
    save_timers(timers)
    return jsonify({"ok":True,"next_spawn":next_spawn.isoformat()})

@app.route("/api/reset", methods=["POST"])
def api_reset():
    data=request.get_json()
    bid=data.get("id")
    timers=load_timers()
    if bid=="all":
        timers.clear()
    else:
        timers.pop(bid,None)
    save_timers(timers)
    return jsonify({"ok":True})

@app.route("/api/settime", methods=["POST"])
def api_settime():
    data=request.get_json()
    bid=data.get("id")
    ns_str=data.get("next_spawn")
    try:
        ns=datetime.datetime.fromisoformat(ns_str.replace("Z",""))
    except:
        return jsonify({"error":"invalid time"}),400
    timers=load_timers()
    timers[bid]={"last_killed":datetime.datetime.now().isoformat(),"next_spawn":ns.isoformat(),"killed_by":"web","notified_10m":False,"notified_spawn":False}
    save_timers(timers)
    return jsonify({"ok":True})

@app.route("/api/timers", methods=["POST"])
def api_post_timers():
    data=request.get_json()
    save_timers(data)
    return jsonify({"ok":True})

application=app

if __name__=="__main__":
    port=int(os.getenv("PORT",10000))
    app.run(host="0.0.0.0",port=port)
