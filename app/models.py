

from datetime import datetime
from . import db



class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200), nullable=False)

    department = db.Column(db.String(50))
    

class Employee(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50))

    movements = db.relationship('Movement', back_populates='employee')

class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))

    tools = db.relationship("Tool", back_populates="category")

class Tool(db.Model):
    __tablename__ = "tools"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    category = db.relationship("Category", back_populates="tools")

    # location info
    loc_row = db.Column(db.Integer, nullable=False)
    loc_col = db.Column(db.Integer, nullable=False)
    loc_shelf = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))

    # status info
    purchase_date = db.Column(db.Date)
    last_maintenance = db.Column(db.Date)
    price = db.Column(db.Float)
    status = db.Column(db.String(20), default='Disponible')  # Disponible, En réparation, Cassé

    movements = db.relationship('Movement', back_populates='tool')

    def __repr__(self):
        return f"<Tool {self.name}>"

class Movement(db.Model):
    __tablename__ = "movements"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    tool_id = db.Column(db.Integer, db.ForeignKey('tools.id'), nullable=False)
    tool = db.relationship('Tool', back_populates='movements')

    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    employee = db.relationship('Employee', back_populates='movements')

    date_emprunt = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime)
    expected_return = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Checked Out')  # Checked Out, Returned
