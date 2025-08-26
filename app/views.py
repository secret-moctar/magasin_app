

from flask import Blueprint, render_template , redirect,url_for
from datetime import datetime, timedelta
from .models import Tool, db

view = Blueprint("view", __name__)

@view.route("/dashboard")
def dashboard():
    # some basic calculation 
    total_tools = db.session.query(Tool).count()


    last_month = datetime.utcnow() - timedelta(days=30)
    tools_last_month = db.session.query(Tool).filter(Tool.purchase_date >= last_month).count()

    
    growth_percent = round((tools_last_month / total_tools * 100),2) if total_tools > 0 else 0

    
    active_tools = db.session.query(Tool).filter(Tool.status == 'Disponible').count()
    active_percent = (active_tools/total_tools * 100) if total_tools >0 else 0
    
    maintenance_tools = db.session.query(Tool).filter(Tool.status == 'En réparation').count()

    
    out_of_service_tools = db.session.query(Tool).filter(Tool.status == 'Cassé').count()

    recent_tools = db.session.query(Tool).order_by(Tool.purchase_date.desc()).limit(20).all()

    return render_template(
        'dashboard.html',
        total_tools=total_tools,
        growth=growth_percent,
        active_tools=active_tools,
        active_percent = active_percent,
        maintenance_tools=maintenance_tools,
        recent_tools=recent_tools,
        out_of_service_tools=out_of_service_tools,
    )
@view.route('/')
def h():
    return redirect('/dashboard')