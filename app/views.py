from flask import Blueprint, render_template, redirect, request, url_for, jsonify, flash
from datetime import datetime, timedelta
from .models import Tool, Movement, Category, Users, Employee, db
from sqlalchemy import event, func

view = Blueprint("view", __name__)

@view.route("/dashboard")
def dashboard():
    # total tools
    total_tools = db.session.query(Tool).count()

    # growth in last month
    last_month = datetime.utcnow() - timedelta(days=30)
    tools_last_month = db.session.query(Tool).filter(Tool.date_ajout >= last_month).count()  # Changed to date_ajout

    growth_percent = round((tools_last_month / total_tools * 100), 2) if total_tools > 0 else 0

    # status counts
    active_tools = db.session.query(Tool).filter(Tool.status == 'Disponible').count()
    active_percent = (active_tools / total_tools * 100) if total_tools > 0 else 0
    emprunt = db.session.query(Tool).filter(Tool.status == 'Emprunté').count()
    maintenance_tools = db.session.query(Tool).filter(Tool.status == 'En réparation').count()
    out_of_service_tools = db.session.query(Tool).filter(Tool.status == 'Cassé').count()

    # recent tools
    recent_tools = db.session.query(Tool).order_by(Tool.date_ajout.desc()).limit(20).all()  # Changed to date_ajout

    # recent borrows (last 20 movements)
    recent_borrows = (
        db.session.query(Movement).join(Tool).filter(Tool.status == 'Emprunté')
        .order_by(Movement.date_emprunt.desc())  # Changed to date_emprunt
        .limit(20)
        .all()
    )

    # Generate alerts for overdue tools
    overdue_tools = (
        db.session.query(Movement, Tool, Employee)
        .join(Tool)
        .join(Employee)
        .filter(Movement.status == 'Checked Out')
        .filter(Movement.expected_return < datetime.utcnow())
        .all()
    )
    
    alerts = []
    for movement, tool, employee in overdue_tools:
        days_overdue = (datetime.utcnow() - movement.expected_return).days
        alerts.append({
            'message': f"Tool '{tool.name}' borrowed by {employee.name} is {days_overdue} days overdue",
            'timestamp': movement.expected_return.strftime('%Y-%m-%d')
        })
    
    return render_template(
        "dashboard.html",
        total_tools=total_tools,
        growth=growth_percent,
        active_tools=active_tools,
        active_percent=active_percent,
        maintenance_tools=maintenance_tools,
        recent_tools=recent_tools,
        out_of_service_tools=out_of_service_tools,
        emprunt=emprunt,
        recent_borrows=recent_borrows,
        alerts=alerts  # Add alerts to template context
    )
@view.route("/cart")
def cart():
    total_tools = db.session.query(Tool).count()


    # status counts
    active_tools = db.session.query(Tool).filter(Tool.status == 'Disponible').count()
    active_percent = (active_tools / total_tools * 100) if total_tools > 0 else 0

    maintenance_tools = db.session.query(Tool).filter(Tool.status == 'En réparation').count()
    out_of_service_tools = db.session.query(Tool).filter(Tool.status == 'Cassé').count()
    

    return jsonify({
        "total_tools": total_tools,
        "active_tools": active_tools,
        "active_percent": active_percent,
        "maintenance_tools": maintenance_tools,
        "out_of_service_tools": out_of_service_tools
    })

@view.route("/tools")
def tools():
    now = datetime.utcnow()
    query = Movement.query.filter(Movement.status == 'Checked Out')
    tool_q = request.args.get('tool')
    emp_q = request.args.get('employee')
    date_emprunt = request.args.get('date_emprunt')
    expected_return = request.args.get('expected_return')
    category = request.args.get('category')
    sort = request.args.get('sort', 'date_emprunt_desc')

    # join
    if tool_q or category:
        query = query.join(Tool)
    if emp_q:
        query = query.join(Employee)

    if tool_q:
        query = query.filter((Tool.name.ilike(f"%{tool_q}%")) | (Tool.id.ilike(f"%{tool_q}%")))
    if emp_q:
        query = query.filter((Employee.name.ilike(f"%{emp_q}%")) | (Employee.id.ilike(f"%{emp_q}%")))
    if date_emprunt:
        try:
            date_obj = datetime.strptime(date_emprunt, '%Y-%m-%d')
            query = query.filter(Movement.date_emprunt >= date_obj)
        except Exception:
            pass
    if expected_return:
        try:
            date_obj = datetime.strptime(expected_return, '%Y-%m-%d')
            query = query.filter(Movement.expected_return <= date_obj)
        except Exception:
            pass
    if category:
        query = query.filter(Tool.category_id == int(category))

    if sort == 'date_emprunt_asc':
        query = query.order_by(Movement.date_emprunt.asc())
    elif sort == 'expected_return_asc':
        query = query.order_by(Movement.expected_return.asc())
    elif sort == 'expected_return_desc':
        query = query.order_by(Movement.expected_return.desc())
    else:
        query = query.order_by(Movement.date_emprunt.desc())

    movements = query.all()
    categories = Category.query.order_by(Category.name).all()
    return render_template("tools.html", movements=movements, now=now, categories=categories)

@view.route("/tools/return/<int:movement_id>", methods=['POST'])
def mark_returned(movement_id):
    movement = Movement.query.get_or_404(movement_id)
    tool = movement.tool
    # json form 
    if request.is_json:
        data = request.get_json()
        tool.loc_shelf = data.get('loc_shelf', tool.loc_shelf)
        tool.loc_col = data.get('loc_col', tool.loc_col)
        tool.loc_row = data.get('loc_row', tool.loc_row)
        new_status = data.get('status', 'Disponible')
    else:
        tool.loc_shelf = request.form.get('loc_shelf', tool.loc_shelf)
        tool.loc_col = request.form.get('loc_col', tool.loc_col)
        tool.loc_row = request.form.get('loc_row', tool.loc_row)
        new_status = request.form.get('status', 'Disponible')
    movement.status = 'Returned'
    tool.status = new_status
    movement.return_date = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('view.tools'))

@view.route("/")
def home_redirect():
    return redirect(url_for("view.dashboard"))

@view.route("/_api_/getcategories")
def categories():
    categories = db.session.query(Category).all()
    data = [{"id": c.id, "name": c.name, "description": c.description} for c in categories]
    return jsonify(data)

@event.listens_for(Movement, "after_insert")
def update_last_checked_out(mapper, connection, target):
    if target.status == "Checked Out":
        connection.execute(
            Tool.__table__.update()
            .where(Tool.id == target.tool_id)
            .values(last_checked_out=target.date_emprunt or datetime.utcnow())
        )

@event.listens_for(Movement, "after_update")
def update_last_checked_out_on_return(mapper, connection, target):
    if target.status == "Checked Out":
        connection.execute(
            Tool.__table__.update()
            .where(Tool.id == target.tool_id)
            .values(last_checked_out=target.date_emprunt or datetime.utcnow())
        )
    elif target.status == "Returned":
        # Reset last_checked_out when returned
        connection.execute(
            Tool.__table__.update()
            .where(Tool.id == target.tool_id)
            .values(last_checked_out=None)
        )
@view.route('/borrows/new', methods=['GET', 'POST'])
def new_borrow():
    from datetime import datetime, timedelta
    if request.method == 'POST':
        tool_id = request.form.get('tool_id')
        employee_id = request.form.get('employee_id')
        expected_return_str = request.form.get('expected_return')

        # expected return date
        try:
            expected_return = datetime.strptime(expected_return_str, '%Y-%m-%d')
            if expected_return <= datetime.utcnow():
                flash("Échec : La date de retour doit être dans le futur.", "danger")
                return redirect(url_for('view.dashboard'))
        except Exception:
            flash("Échec : Date de retour prévue invalide.", "danger")
            return redirect(url_for('view.dashboard'))

        # validatio
        tool = Tool.query.get(tool_id)
        employee = Employee.query.get(employee_id)
        if not tool or tool.status != 'Disponible' or not employee:
            flash("Échec : Outil ou employé invalide.", "danger")
            return redirect(url_for('view.dashboard'))

        # Create movement
        movement = Movement(
            tool_id=tool_id,
            employee_id=employee_id,
            date_emprunt=datetime.utcnow(),
            expected_return=expected_return,
            status='Checked Out'
        )
        db.session.add(movement)
        tool.status = 'Emprunté'
        db.session.commit()
        flash("Créé avec succès !", "success")
        return redirect(url_for('view.dashboard'))

    employees = Employee.query.all()
    return render_template('borrow.html', employees=employees, datetime=datetime, timedelta=timedelta)

@view.route("/employees/add", methods=["POST"])
def add_employee():
    if request.method == "POST":
        employee_id = request.form.get("employee_id")
        name = request.form.get("employee_name")
        department = request.form.get("employee_department")
        
        # Check if employee already exists
        existing_employee = Employee.query.get(employee_id)
        if existing_employee:
            return jsonify({"success": False, "message": "Employee ID already exists"})
        
        # Create new employee
        new_employee = Employee(
            id=employee_id,
            name=name,
            department=department
        )
        
        db.session.add(new_employee)
        db.session.commit()
        
        return jsonify({"success": True, "employee": {"id": new_employee.id, "name": new_employee.name}})
    





@view.route("/find-tools", methods=["GET"])


def find_tools():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    # Search ID or Name
    tools = Tool.query.filter(
        (Tool.name.ilike(f"%{query}%")) | (Tool.id.ilike(f"%{query}%"))
    ).all()

    results = [
        {
            "id": tool.id,
            "name": tool.name,
            "loc_row": tool.loc_row,
            "loc_col": tool.loc_col,
            "loc_shelf": tool.loc_shelf,
            "status": tool.status,
        }
        for tool in tools
    ]
    print (results)
    return jsonify(results)




# serz
def serialize_tool(tool):
    return {
        "id": tool.id,
        "name": tool.name,
        "category": tool.category.name if getattr(tool, "category", None) else None,
        "loc_row": tool.loc_row,
        "loc_col": tool.loc_col,
        "loc_shelf": tool.loc_shelf,
        "description": tool.description,
        "date_ajout": tool.date_ajout.isoformat() if tool.date_ajout else None,
        "purchase_date": tool.purchase_date.isoformat() if tool.purchase_date else None,
        "last_maintenance": tool.last_maintenance.isoformat() if tool.last_maintenance else None,
        "last_checked_out": tool.last_checked_out.isoformat() if tool.last_checked_out else None,
        "price": tool.price,
        "status": tool.status,
        "photo": tool.photo or None
    }

def serialize_movement(mov):
    return {
        "id": mov.id,
        "tool_id": mov.tool_id,
        "tool_name": mov.tool.name if mov.tool else None,
        "employee_id": mov.employee_id,
        "employee_name": mov.employee.name if mov.employee else None,
        "date_emprunt": mov.date_emprunt.isoformat() if mov.date_emprunt else None,
        "return_date": mov.return_date.isoformat() if mov.return_date else None,
        "expected_return": mov.expected_return.isoformat() if mov.expected_return else None,
        "status": mov.status
    }

# ---- Main page -----------------------------------------------------------
@view.route('/inventory')
def inventory():
    # Stats
    total_tools = db.session.query(func.count(Tool.id)).scalar() or 0
    available_tools = db.session.query(func.count(Tool.id)).filter(Tool.status == 'Disponible').scalar() or 0
    maintenance_tools = db.session.query(func.count(Tool.id)).filter(Tool.status == 'En réparation').scalar() or 0
    borrowed_tools = db.session.query(func.count(Movement.id)).filter(Movement.status == 'Checked Out').scalar() or 0

    # All tools (with info)
    all_tools = db.session.query(Tool).order_by(Tool.date_ajout.desc()).all()

    # For filters
    categories = db.session.query(Category).order_by(Category.name).all()
    employees = db.session.query(Employee).order_by(Employee.name).all()

    # Recent lists
    recent_tools = db.session.query(Tool).order_by(Tool.date_ajout.desc()).limit(20).all()
    recent_borrows = db.session.query(Movement).order_by(Movement.date_emprunt.desc()).limit(20).all()

    # Serialize all tools with extra info
    def serialize_tool_full(tool):
        movement = db.session.query(Movement).filter(Movement.tool_id == tool.id).order_by(Movement.date_emprunt.desc()).first()
        return {
            "id": tool.id,
            "name": tool.name,
            "category": tool.category.name if tool.category else None,
            "loc_row": tool.loc_row,
            "loc_col": tool.loc_col,
            "loc_shelf": tool.loc_shelf,
            "description": tool.description,
            "date_ajout": tool.date_ajout.isoformat() if tool.date_ajout else None,
            "purchase_date": tool.purchase_date.isoformat() if tool.purchase_date else None,
            "last_maintenance": tool.last_maintenance.isoformat() if tool.last_maintenance else None,
            "price": tool.price,
            "status": tool.status,
            "photo": tool.photo or None,
            "last_checked_out": tool.last_checked_out.isoformat() if tool.last_checked_out else None,
            "borrowed_by": movement.employee.name if movement and movement.status == "Checked Out" and movement.employee else None,
            "date_emprunt": movement.date_emprunt.isoformat() if movement and movement.status == "Checked Out" and movement.date_emprunt else None,
            "expected_return": movement.expected_return.isoformat() if movement and movement.status == "Checked Out" and movement.expected_return else None,
            "return_date": movement.return_date.isoformat() if movement and movement.status == "Returned" and movement.return_date else None
        }

    all_tools_json = [serialize_tool_full(t) for t in all_tools]

    return render_template(
        "inventory.html",
        total_tools=total_tools,
        available_tools=available_tools,
        maintenance_tools=maintenance_tools,
        borrowed_tools=borrowed_tools,
        categories=categories,
        employees=employees,
        all_tools_json=all_tools_json,
        recent_tools=recent_tools,
        recent_borrows=recent_borrows
    )


def serialize_tool_full(tool):
        movement = db.session.query(Movement).filter(Movement.tool_id == tool.id).order_by(Movement.date_emprunt.desc()).first()
        return {
            "id": tool.id,
            "name": tool.name,
            "category": tool.category.name if tool.category else None,
            "loc_row": tool.loc_row,
            "loc_col": tool.loc_col,
            "loc_shelf": tool.loc_shelf,
            "description": tool.description,
            "date_ajout": tool.date_ajout.isoformat() if tool.date_ajout else None,
            "purchase_date": tool.purchase_date.isoformat() if tool.purchase_date else None,
            "last_maintenance": tool.last_maintenance.isoformat() if tool.last_maintenance else None,
            "price": tool.price,
            "status": tool.status,
            "photo": tool.photo or None,
            "last_checked_out": tool.last_checked_out.isoformat() if tool.last_checked_out else None,
            "borrowed_by": movement.employee.name if movement and movement.status == "Checked Out" and movement.employee else None,
            "date_emprunt": movement.date_emprunt.isoformat() if movement and movement.status == "Checked Out" and movement.date_emprunt else None,
            "expected_return": movement.expected_return.isoformat() if movement and movement.status == "Checked Out" and movement.expected_return else None,
            "return_date": movement.return_date.isoformat() if movement and movement.status == "Returned" and movement.return_date else None
        }
@view.route('/api/tools')
def api_tools():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 12))
    q = request.args.get('q', '').strip()
    status = request.args.get('status')
    category_id = request.args.get('category')
    employee_id = request.args.get('employee_id')

    query = db.session.query(Tool)
    if q:
        ilike = func.lower(Tool.name).like(f"%{q.lower()}%") | func.lower(Tool.id).like(f"%{q.lower()}%")
        query = query.filter(ilike)
    if status:
        query = query.filter(Tool.status == status)
    if category_id:
        try:
            query = query.filter(Tool.category_id == int(category_id))
        except ValueError:
            pass
    if employee_id:
        query = query.join(Movement).filter(Movement.employee_id == employee_id, Movement.status == "Checked Out")

    total = query.count()
    items = query.order_by(Tool.date_ajout.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": [serialize_tool_full(t) for t in items]
    })

@view.route('/api/categories')
def api_categories():
    cats = db.session.query(Category).order_by(Category.name).all()
    return jsonify([{"id": c.id, "name": c.name} for c in cats])

@view.route('/api/employees')
def api_employees():
    emps = db.session.query(Employee).order_by(Employee.name).all()
    return jsonify([{"id": e.id, "name": e.name} for e in emps])

@view.route('/api/stats')
def api_stats():
    total_tools = db.session.query(func.count(Tool.id)).scalar() or 0
    available_tools = db.session.query(func.count(Tool.id)).filter(Tool.status == 'Disponible').scalar() or 0
    maintenance_tools = db.session.query(func.count(Tool.id)).filter(Tool.status == 'En réparation').scalar() or 0
    borrowed_movements_count = db.session.query(func.count(Movement.id)).filter(Movement.status == 'Checked Out').scalar() or 0
    return jsonify({
        "total_tools": total_tools,
        "available_tools": available_tools,
        "maintenance_tools": maintenance_tools,
        "borrowed_tools": borrowed_movements_count
    })

@view.route('/api/recent-borrows')
def api_recent_borrows():
    items = db.session.query(Movement).order_by(Movement.date_emprunt.desc()).limit(20).all()
    return jsonify([serialize_movement(m) for m in items])

@view.route('/add-tool', methods=['GET', 'POST'])
def add_tool():
    if request.method == 'POST':
        tool = Tool(
            id=request.form['id'],
            name=request.form['name'],
            category_id=request.form['category_id'],
            loc_row=request.form['loc_row'],
            loc_col=request.form['loc_col'],
            loc_shelf=request.form['loc_shelf'],
            description=request.form.get('description', ''),
            status=request.form['status'],
            photo=request.form.get('photo', '')
        )
        db.session.add(tool)
        db.session.commit()
        return redirect(url_for('view.inventory'))
    categories = db.session.query(Category).order_by(Category.name).all()
    return render_template('add_tool.html', categories=categories)

@view.route("/find-employees", methods=["GET"])
def find_employees():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])
    employees = Employee.query.filter(
        (Employee.name.ilike(f"%{query}%")) | (Employee.id.ilike(f"%{query}%"))
    ).all()
    results = [
        {
            "id": emp.id,
            "name": emp.name,
            "department": emp.department
        }
        for emp in employees
    ]
    return jsonify(results)

@view.route("/maintenance")
def maintenance():
    categories = Category.query.order_by(Category.name).all()
    return render_template("maintenance.html", categories=categories)

@view.route("/api/maintenance-tools")
def api_maintenance_tools():
    q = request.args.get('q', '').strip()
    status = request.args.get('status')
    category_id = request.args.get('category')

    query = db.session.query(Tool).filter(Tool.status.in_(['Disponible', 'Cassé', 'En réparation']))
    if q:
        ilike = func.lower(Tool.name).like(f"%{q.lower()}%") | func.lower(Tool.id).like(f"%{q.lower()}%")
        query = query.filter(ilike)
    if status:
        query = query.filter(Tool.status == status)
    if category_id:
        try:
            query = query.filter(Tool.category_id == int(category_id))
        except ValueError:
            pass
    items = query.order_by(Tool.date_ajout.desc()).all()
    return jsonify({
        "items": [serialize_tool(t) for t in items]
    })

@view.route("/maintenance/send/<tool_id>", methods=["POST"])
def send_to_maintenance(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    data = request.get_json()
    expected_return_str = data.get('expected_return')
    try:
        expected_return = datetime.strptime(expected_return_str, '%Y-%m-%d')
    except Exception:
        return jsonify({"success": False, "message": "Date invalide"}), 400

    # Create a movement for maintenance
    movement = Movement(
        tool_id=tool.id,
        employee_id=None,
        date_emprunt=datetime.utcnow(),
        expected_return=expected_return,
        status='En réparation'
    )
    db.session.add(movement)
    tool.status = 'En réparation'
    db.session.commit()
    return jsonify({"success": True})

@view.route("/maintenance/return/<tool_id>", methods=["POST"])
def maintenance_return(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    data = request.get_json()
    employee_id = data.get('employee_id')
    status = data.get('status', 'Disponible')
    loc_shelf = data.get('loc_shelf')
    loc_col = data.get('loc_col')
    loc_row = data.get('loc_row')

    # Update tool location and status
    tool.loc_shelf = loc_shelf
    tool.loc_col = loc_col
    tool.loc_row = loc_row
    tool.status = status

    # Record movement for the repair
    movement = Movement(
        tool_id=tool.id,
        employee_id=employee_id,
        date_emprunt=datetime.utcnow(),
        expected_return=datetime.utcnow(),
        status='Returned'
    )
    db.session.add(movement)
    db.session.commit()
    return jsonify({"success": True})

@view.route('/api/categories', methods=['POST'])
def add_category():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if not name:
        return jsonify({"success": False, "message": "Category name is required"}), 400
    # Check for duplicate
    if db.session.query(Category).filter_by(name=name).first():
        return jsonify({"success": False, "message": "Category already exists"}), 400
    cat = Category(name=name, description=description)
    db.session.add(cat)
    db.session.commit()
    return jsonify({"success": True, "id": cat.id, "name": cat.name})

@view.route("/movements")
def movements():
    categories = Category.query.order_by(Category.name).all()
    return render_template("movements.html", categories=categories)

@view.route("/api/movements")
def api_movements():
    tool_q = request.args.get('tool', '').strip()
    emp_q = request.args.get('employee', '').strip()
    status = request.args.get('status')
    date = request.args.get('date')
    query = db.session.query(Movement).join(Tool).outerjoin(Employee)
    if tool_q:
        query = query.filter((Tool.name.ilike(f"%{tool_q}%")) | (Tool.id.ilike(f"%{tool_q}%")))
    if emp_q:
        query = query.filter((Employee.name.ilike(f"%{emp_q}%")) | (Employee.id.ilike(f"%{emp_q}%")))
    if status:
        query = query.filter(Movement.status == status)
    if date:
        try:
            from datetime import datetime, timedelta
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            next_day = date_obj + timedelta(days=1)
            query = query.filter(Movement.date_emprunt >= date_obj, Movement.date_emprunt < next_day)
        except Exception:
            pass
    query = query.order_by(Movement.date_emprunt.desc())
    movements = query.all()
    def serialize_movement_full(mov):
        return {
            "id": mov.id,
            "tool_id": mov.tool_id,
            "tool_name": mov.tool.name if mov.tool else None,
            "tool_photo": mov.tool.photo if mov.tool and mov.tool.photo else None,
            "employee_id": mov.employee_id,
            "employee_name": mov.employee.name if mov.employee else None,
            "date_emprunt": mov.date_emprunt.isoformat() if mov.date_emprunt else None,
            "return_date": mov.return_date.isoformat() if mov.return_date else None,
            "expected_return": mov.expected_return.isoformat() if mov.expected_return else None,
            "status": mov.status
        }
    return jsonify([serialize_movement_full(m) for m in movements])

@view.route("/report")
def report():
    return render_template("report.html")

@view.route("/api/overdue")
def api_overdue():
    tool_q = request.args.get('tool', '').strip()
    emp_q = request.args.get('employee', '').strip()
    date = request.args.get('date')
    now = datetime.utcnow()
    query = db.session.query(Movement).join(Tool).outerjoin(Employee).filter(
        Movement.status == 'Checked Out',
        Movement.expected_return < now
    )
    if tool_q:
        query = query.filter((Tool.name.ilike(f"%{tool_q}%")) | (Tool.id.ilike(f"%{tool_q}%")))
    if emp_q:
        query = query.filter((Employee.name.ilike(f"%{emp_q}%")) | (Employee.id.ilike(f"%{emp_q}%")))
    if date:
        try:
            from datetime import datetime, timedelta
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            next_day = date_obj + timedelta(days=1)
            query = query.filter(Movement.expected_return >= date_obj, Movement.expected_return < next_day)
        except Exception:
            pass
    query = query.order_by(Movement.expected_return.asc())
    overdues = query.all()
    def serialize_overdue(mov):
        days_overdue = (now - mov.expected_return).days
        return {
            "id": mov.id,
            "tool_id": mov.tool_id,
            "tool_name": mov.tool.name if mov.tool else None,
            "tool_photo": mov.tool.photo if mov.tool and mov.tool.photo else None,
            "employee_id": mov.employee_id,
            "employee_name": mov.employee.name if mov.employee else None,
            "date_emprunt": mov.date_emprunt.isoformat() if mov.date_emprunt else None,
            "expected_return": mov.expected_return.isoformat() if mov.expected_return else None,
            "days_overdue": days_overdue
        }
    return jsonify([serialize_overdue(m) for m in overdues])
