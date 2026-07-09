"""
PayOptimise Suite — Main Application Entry Point
MS5132 Major ISM Project | Jane Donisha Masila Clement Valavan
University of Galway, 2025-2026
Run: python app.py  →  open http://localhost:5000
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os, sys, random

sys.path.insert(0, os.path.dirname(__file__))

from backend.data_generator  import generate_dataset, get_summary_stats
from backend.ab_engine        import ABExperimentEngine, run_all_experiments
from backend.recommender      import HybridRecommender, FeatureStore, DEFAULT_METHODS
from backend.funnel_analytics import FunnelAnalytics
from backend.database         import db_init, db_log_session, db_get_sessions, db_get_stats

# Flask default: looks for templates/ and static/ automatically
app = Flask(__name__)
CORS(app)

_df = _store = _rec = _fa = None

def get_data():
    global _df, _store, _rec, _fa
    if _df is None:
        print("Generating 20,000-session dataset...")
        _df    = generate_dataset(n=20000)
        _store = FeatureStore.from_dataframe(_df)
        _rec   = HybridRecommender(_store)
        _fa    = FunnelAnalytics(_df)
        print(f"Ready — conv={_df.converted.mean():.1%}")
    return _df, _store, _rec, _fa

@app.route('/')
def index():           return render_template('index.html')
@app.route('/dashboard')
def dashboard():       return render_template('dashboard.html')
@app.route('/experiments')
def experiments():     return render_template('experiments.html')
@app.route('/recommendations')
def recommendations(): return render_template('recommendations.html')
@app.route('/simulator')
def simulator():       return render_template('simulator.html')

@app.route('/api/stats')
def api_stats():
    df,_,_,_ = get_data()
    return jsonify(get_summary_stats(df))

@app.route('/api/funnel')
def api_funnel():
    seg = request.args.get('segment')
    val = request.args.get('value')
    df,_,_,fa = get_data()
    summary = fa.funnel_summary(seg, val) if seg and val else fa.funnel_summary()
    return jsonify({'funnel': summary.to_dict('records'),
                    'alerts': fa.friction_alerts(0.12),
                    'comparison': fa.compare_conditions().to_dict('records'),
                    'cohorts': fa.cohort_comparison('device').to_dict('records')})

@app.route('/api/experiments')
def api_experiments():
    df,_,_,_ = get_data()
    return jsonify(run_all_experiments(df).to_dict('records'))

@app.route('/api/recommend')
def api_recommend():
    device  = request.args.get('device','mobile')
    hour    = int(request.args.get('hour',13))
    depth   = int(request.args.get('depth',3))
    user_id = request.args.get('user_id','demo')
    is_peak = int(12<=hour<=14 or 19<=hour<=21)
    _,store,rec,_ = get_data()
    recs = rec.recommend(user_id, DEFAULT_METHODS,
                         {'device':device,'hour':hour,'page_depth':depth,'is_peak':is_peak}, top_k=3)
    return jsonify([{'rank':i+1,'method':r.method.name,'score':r.score,'reasons':r.reasons}
                    for i,r in enumerate(recs)])

@app.route('/api/recommend/ctr')
def api_recommend_ctr():
    df,_,rec,_ = get_data()
    return jsonify(rec.evaluate_ctr(df))

@app.route('/api/recommend/features')
def api_recommend_features():
    return jsonify([
        {'feature':'Collaborative filtering','weight':0.40,'color':'#3b82f6'},
        {'feature':'Device type match',      'weight':0.31,'color':'#14b8a6'},
        {'feature':'Time of day context',    'weight':0.22,'color':'#f59e0b'},
        {'feature':'Session depth (intent)', 'weight':0.07,'color':'#64748b'},
    ])

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    data   = request.get_json() or {}
    device = data.get('device','mobile')
    auth   = data.get('auth','biometric')
    rec_on = data.get('rec_on',True)
    tenure = data.get('tenure','returning')
    hour   = int(data.get('hour',13))
    loyal  = tenure == 'loyal'
    DROP = {
        'onboarding':    {'mobile':0.13 if rec_on else 0.20,'desktop':0.09 if rec_on else 0.12},
        'payment_init':  {'mobile':0.12 if rec_on else 0.22,'desktop':0.10 if rec_on else 0.15},
        'authentication':{'mobile':0.14 if auth=='biometric' else 0.43,
                          'desktop':0.10 if auth=='biometric' else 0.28},
        'confirmation':  {'mobile':0.06,'desktop':0.04},
    }
    if loyal:
        DROP = {k:{d:v*0.75 for d,v in inner.items()} for k,inner in DROP.items()}
    journey = []
    for stage, probs in DROP.items():
        p = probs[device]; r = random.random(); passed = r >= p
        journey.append({'stage':stage,'passed':passed,'p_drop':round(p*100,1),'rolled':round(r,3)})
        if not passed: break
    converted  = all(s['passed'] for s in journey) and len(journey)==4
    drop_stage = next((s['stage'] for s in journey if not s['passed']), None)
    sugg = {'onboarding':'Run A/B: 2-step vs 4-step onboarding',
            'payment_init':'Enable personalised recommendations (+107% CTR)',
            'authentication':'Switch to biometric auth — reduces drop-off by 65%',
            'confirmation':'Improve fee transparency'}
    return jsonify({'journey':journey,'converted':converted,
                    'drop_stage':drop_stage,'suggestion':sugg.get(drop_stage,'')})

@app.route('/api/db/sessions')
def api_db_sessions():
    return jsonify(db_get_sessions(int(request.args.get('limit',50))))

@app.route('/api/db/stats')
def api_db_stats():
    return jsonify(db_get_stats())

@app.route('/api/db/log', methods=['POST'])
def api_db_log():
    db_log_session(request.get_json() or {})
    return jsonify({'status':'ok'})

if __name__ == '__main__':
    print("\n PayOptimise Suite — http://localhost:5000\n")
    db_init()
    get_data()
    app.run(debug=True, port=5000, host='0.0.0.0')
