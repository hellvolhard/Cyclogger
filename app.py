from flask import Flask, redirect, request_tearing_down, url_for, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

def page_not_found(e):
  return render_template('404.html'), 404
app = Flask(__name__)
app.register_error_handler(404, page_not_found)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite3"
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()

class Auth(db.Model):
    __tablename__ = 'Authorization'
    auth_id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False, unique=True)
    email_id = db.Column(db.String, unique=True, nullable=False)
    full_name = db.Column(db.String,  nullable=False)
    password = db.Column(db.String(128),  nullable=False)
    child = db.relationship('Tracker', backref='Authorization', passive_deletes=True )

class Tracker(db.Model):
    __tablename__ = 'Tracker'
    tracker_id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Authorization.auth_id", ondelete='CASCADE'), nullable=False)
    tracker_name = db.Column(db.String,  nullable=False)
    tracker_desc = db.Column(db.String,  nullable=False)
    child = db.relationship('Logs', backref='Tracker', passive_deletes=True)

class Logs(db.Model):
    __tablename__ = 'Logs'
    log_id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False, unique=True)
    tlog_id = db.Column(db.Integer, db.ForeignKey("Tracker.tracker_id", ondelete='CASCADE'), nullable=False)
    log_dist = db.Column(db.Integer,  nullable=False)
    log_comm = db.Column(db.String,  nullable=True)
    log_timestamp = db.Column(db.Date,  nullable=False)
    log_dur = db.Column(db.Integer, nullable=False)

db.create_all()
db.session.commit()

def chk_pswd(passwd):
      
    SS =['$', '@', '#', '%']
    val = True
      
    if len(passwd) < 6:
        print('length should be at least 6')
        val = False
          
    if len(passwd) > 20:
        print('length should be not be greater than 8')
        val = False
          
    if not any(char.isdigit() for char in passwd):
        print('Password should have at least one numeral')
        val = False
          
    if not any(char.isupper() for char in passwd):
        print('Password should have at least one uppercase letter')
        val = False
          
    if not any(char.islower() for char in passwd):
        print('Password should have at least one lowercase letter')
        val = False
          
    if not any(char in SS for char in passwd):
        print('Password should have at least one of the symbols $@#')
        val = False
    if val:
        return val

def avg_graph(activity_id, values):
    plot_x = []
    for val1 in values:
        plot_x.append(val1.log_timestamp)
    plot_y = []
    plot_z = []
    for val2 in values:
        plot_y.append((val2.log_dist/val2.log_dur))

    graph = pd.DataFrame(plot_y, plot_x)
    try:
        graph_plot=graph.plot(kind='line', grid=False, title="Activities", ylabel="Average Speed", xlabel="Date").get_figure()
        graph_path_avg = "static/graphs/log" + str(activity_id) + "_avg.png"
        graph_plot.savefig(graph_path_avg)
        return graph_path_avg
    except:
        graph_path = "static/graphs/log0.png"
        return graph_path

def graph(activity_id, values):
    plot_x = []
    for val1 in values:
        plot_x.append(val1.log_timestamp)
    plot_y = []
    for val2 in values:
        plot_y.append(val2.log_dist)

    graph = pd.DataFrame(plot_y, plot_x)
    try:
        graph_plot=graph.plot(kind='bar', grid=False, title="Activities", ylabel="Distance", xlabel="Date").get_figure()
        graph_path = "static/graphs/log" + str(activity_id) + ".png"
        graph_plot.savefig(graph_path)
        return graph_path
    except:
        graph_path = "static/graphs/log0.png"
        return graph_path
    
@app.route("/signup", methods = ["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("signup.html")
    if request.method == "POST":
        email = request.form["eid"]
        fullname = request.form["fn"]
        passwd = request.form["pswd"]
        
        track = Tracker.query.all()
        auth = Auth.query.all()
        log = Logs.query.all()
        try:
            for user in auth:
                if user.email_id == email:
                    return redirect(url_for("register"))
        except:
            return render_template('error.html')
        
        try: 
            if chk_pswd(passwd):
                hashed_pwd = generate_password_hash(passwd, method = "sha256")
                auth_n = Auth(email_id=email, full_name= fullname, password = hashed_pwd )
                db.session.add(auth_n)
                db.session.commit()
                return redirect(url_for("authentication"))
            else:
                return redirect(url_for("register"))
        except:
            return render_template('error.html')

@app.route("/", methods=["GET", "POST"])
def authentication():
    error = None
    try:
        if request.method == "GET":
            return render_template("login.html")
    except:
        return render_template('error.html')
    try:    
        if request.method == "POST":
            auth = Auth.query.all()
            email = request.form["eid"]
            password = request.form["pswd"]
            for au in auth:
                if email == au.email_id and check_password_hash(au.password, password):
                    auth_cur= Auth.query.filter(Auth.email_id == email).one()
                    au_id = auth_cur.auth_id
                    return redirect(url_for("dashboard", au_id=au_id))
        return redirect(url_for("authentication"))
    except:
        return render_template('error.html')

@app.route("/dashboard/<int:au_id>", methods = ["GET", "POST"])
def dashboard(au_id):
    
    try:
        if request.method == "GET":
            activity = Tracker.query.filter(Tracker.user_id == au_id)
            actlist = []
            activelist = []
            for act in activity:
                actlist.append(act.tracker_id)
                activelist.append((act.tracker_id,act.tracker_name))
            usr_curr = Auth.query.filter(Auth.auth_id == au_id).one()
            loglist = []
            lgs = Logs.query.filter(Logs.tlog_id.in_(actlist)).order_by(Logs.log_id.desc()).limit(5).all()
            for Log in lgs:
                for t in activelist:
                    if Log.tlog_id == t[0]:
                        loglist.append((t[1], Log.log_dist, Log.log_dur, Log.log_comm,Log.log_timestamp, t[0]))
            return render_template("dashboard.html",loglist=loglist, activity=activity, au_id=au_id, usr_name=usr_curr.full_name)
    except:
        return render_template('error.html')


@app.route("/<int:au_id>/<int:activity_id>", methods=["GET", "POST"])
def activity(activity_id, au_id):
    try:   
        if request.method=="GET":
            active = Tracker.query.filter(Tracker.tracker_id == activity_id).one()
            activity= Tracker.query.filter(Tracker.user_id == au_id)
            lgs = Logs.query.filter(Logs.tlog_id == activity_id)
            usr_curr = Auth.query.filter(Auth.auth_id == au_id).one()
            plot_path = graph(activity_id,lgs)
            plot_avg_path = avg_graph(activity_id,lgs)
            return render_template("tracker.html", active=active, activity=activity, lgs=lgs, au_id=au_id, usr_name=usr_curr.full_name, plot_path=plot_path, plot_avg_path=plot_avg_path )
    except:
        return render_template('error.html')
        
    try:
        if request.method=="POST":
            dateinp = request.form["dat"]
            dt = datetime.strptime(dateinp, '%Y-%m-%d')
            dist = request.form["dist"]
            tim = request.form["dur"]
            notes = request.form["notes"] 
    except:
        return render_template('error.html')    

    act_new= Logs(tlog_id=activity_id, log_dist=dist,log_comm=notes, log_dur=tim,log_timestamp=dt )
    db.session.add(act_new)
    db.session.commit()
    return redirect(url_for("activity", activity_id=activity_id, au_id=au_id))

@app.route("/create/<int:au_id>", methods=["GET", "POST"])
def add_activity(au_id):
    try:        
        if request.method=="GET":
            
            activity = Tracker.query.filter(Tracker.user_id == au_id)
            usr_curr = Auth.query.filter(Auth.auth_id == au_id).first()
            usr_name = usr_curr.full_name
            return render_template("addtracker.html", activity=activity,au_id=au_id, usr_name=usr_name)
    except:
        return render_template('error.html')

    try:
        if request.method=="POST":
            actname = request.form["actname"]
            actdesc = request.form["actdesc"]
            #print(tname,tdesc,ttype)
            act_u = Tracker(user_id=au_id)
            act_un=Tracker(tracker_name=actname)
            act_ud=Tracker(tracker_desc=actdesc)
            act_new = Tracker(user_id=au_id, tracker_name=actname, tracker_desc=actdesc)
            db.session.add(act_new)
            db.session.commit()
            return redirect(url_for("add_activity", au_id=au_id))
    except:
        return render_template('error.html')

@app.route("/logupdate/<int:au_id>/<int:activity_id>/<int:lgid>", methods=["GET", "POST"])
def update_logs(activity_id, au_id, lgid):
    try:    
        if request.method=="GET":
            lgs = Logs.query.filter(Logs.log_id == lgid).one()
            trackers = Tracker.query.filter(Tracker.user_id == au_id)
            usr_curr = Auth.query.filter(Auth.auth_id == au_id).first()
            usr_name = usr_curr.full_name
            return render_template("updatelog.html", au_id=au_id, trackers=trackers, usr_name=usr_name, lgid=lgid, activity_id=activity_id, lgs=lgs)
    except:
        return render_template('error.html')
    try:
        if request.method=="POST":
            lgs = Logs.query.filter(Logs.log_id == lgid).one()
            dateinp = request.form["dat"]
            dt = datetime.strptime(dateinp, '%Y-%m-%d')
            lgs.log_timestamp = dt
            lgs.log_dur = request.form["dur"]
            lgs.log_dist = request.form["dist"]
            lgs.log_comm = request.form["notes"]
            db.session.commit()
            return redirect(url_for("activity", activity_id=activity_id, au_id=au_id))
    except:
        return render_template('error.html')

@app.route("/update/<int:au_id>/<int:activity_id>", methods=["GET", "POST"])
def update_activity(au_id, activity_id):
    try:
        if request.method=="GET":
            activity = Tracker.query.filter(Tracker.user_id == au_id)
            usr_curr = Auth.query.filter(Auth.auth_id == au_id).first()
            return render_template("updatetracker.html", activity=activity,au_id=au_id, activity_id=activity_id, usr_name=usr_curr.full_name)
    except:
        return render_template('error.html')

    try:
        if request.method=="POST":
            act = Tracker.query.filter(Tracker.tracker_id==activity_id).one()
            act.tracker_name = request.form["tname"]
            act.tracker_desc = request.form["tdesc"]
            db.session.commit()
            return redirect(url_for("dashboard", au_id=au_id))
    except:
        return render_template('error.html')

@app.route("/updateuser/<int:au_id>", methods = ["GET", "POST"])
def update_user(au_id):
   
    if request.method=="GET":
        auth=Auth.query.filter(Auth.auth_id == au_id).one()
        usr_curr = Auth.query.filter(Auth.auth_id == au_id).first()
        return render_template("updateuser.html", auth=auth, au_id=au_id, usr_name=usr_curr.full_name)

    if request.method=="POST":
        auth=Auth.query.filter(Auth.auth_id == au_id).one()
        auth.email_id= request.form["newemail"]
        auth.full_name= request.form["newfname"]
        new_pass= request.form["newpass"]
        hashed_pwd = generate_password_hash(new_pass, method = "sha256")
        auth.password=hashed_pwd
        db.session.commit()
        return redirect(url_for("dashboard", au_id= au_id))

@app.route("/dellog/<int:au_id>/<int:activity_id>/<int:lgid>", methods=["GET", "POST"])
def log_d(activity_id, au_id, lgid):
    try:
        if request.method=="GET":
            lg = Logs.query.filter(Logs.log_id == lgid).first()
            db.session.delete(lg)
            db.session.commit()
            return redirect(url_for("activity", activity_id=activity_id, au_id=au_id))
    except:
        return render_template('error.html')


@app.route("/delact/<int:au_id>/<int:activity_id>", methods=["GET", "POST"])
def act_d(activity_id, au_id):
    try:
        if request.method=="GET":
            lg = Logs.query.filter(Logs.tlog_id == activity_id)
            for l in lg:
                db.session.delete(l)
            db.session.commit()
            act_del = Tracker.query.filter(Tracker.tracker_id == activity_id).first()
            db.session.delete(act_del)
            db.session.commit()
            return redirect(url_for("dashboard", au_id=au_id))
    except:
        return render_template('error.html')

@app.route("/delete_user/<int:au_id>", methods=["GET", "POST"])
def delete_user(au_id):
    if request.method=="GET":
        #user delete
        au = Auth.query.filter(Auth.auth_id == au_id).one()
        act_del = Tracker.query.filter(Tracker.user_id == au_id)
        listrack=[]
        for l in act_del:
            listrack.append(l.tracker_id)

        lgs = Logs.__table__.delete().where(Logs.tlog_id.in_(listrack))
        db.session.execute(lgs)
        db.session.commit()
        for tr in act_del:
            db.session.delete(tr)
            db.session.commit()
        db.session.delete(au)
        db.session.commit()
        return redirect(url_for("authentication"))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404

if __name__ == '__main__':
  # Run the Flask app
  app.run(debug=True)