import mysql.connector
from datetime import datetime, timedelta
import random
import faker

fake = faker.Faker()

# ---------- Database connection ----------
config = {
    'user': 'root',  # replace with your MySQL username
    'password': '7152',  # replace with your MySQL password
    'host': 'localhost',
    'database': 'magasin_outillages',  # replace with your DB name
    'auth_plugin': 'mysql_native_password'  # avoid caching_sha2_password issues
}

cnx = mysql.connector.connect(**config)
cursor = cnx.cursor()
print("Connected to MySQL database.")

# ---------- Helper function ----------
def random_date(start_year=2018, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

# ---------- Insert employees ----------
employees = [(fake.name(), random.choice(['Maintenance', 'Logistics', 'Administration', 'IT'])) for _ in range(20)]
cursor.executemany("INSERT INTO employees (name, department) VALUES (%s, %s)", employees)
cnx.commit()
print("Inserted 20 employees.")

# ---------- Insert users ----------
users = [
    ('Admin User', 'admin@example.com', 'admin123', 'Administration'),
    ('Regular User', 'user@example.com', 'user123', 'Maintenance')
]
cursor.executemany("INSERT INTO users (name, email, password, department) VALUES (%s, %s, %s, %s)", users)
cnx.commit()
print("Inserted 2 users.")

# ---------- Insert categories ----------
category_names = ['Hand Tools', 'Power Tools', 'Safety Equipment', 'Measuring Instruments', 'Electrical']
categories = [(name, fake.sentence(nb_words=5)) for name in category_names]
cursor.executemany("INSERT INTO categories (name, description) VALUES (%s, %s)", categories)
cnx.commit()
print("Inserted categories.")

# Get category IDs
cursor.execute("SELECT id FROM categories")
category_ids = [row[0] for row in cursor.fetchall()]

# ---------- Insert tools ----------
tools = []
for _ in range(200):
    name = fake.word().capitalize() + " Tool"
    category_id = random.choice(category_ids)
    loc_row = random.randint(1, 10)
    loc_col = random.randint(1, 10)
    loc_shelf = random.randint(1, 5)
    description = fake.sentence(nb_words=6)
    purchase_date = random_date()
    last_maintenance = purchase_date + timedelta(days=random.randint(30, 500))
    price = round(random.uniform(10.0, 1000.0), 2)
    status = random.choice(['Disponible', 'En réparation', 'Cassé'])
    tools.append((name, category_id, loc_row, loc_col, loc_shelf, description, purchase_date, last_maintenance, price, status))

cursor.executemany("""
    INSERT INTO tools
    (name, category_id, loc_row, loc_col, loc_shelf, description, purchase_date, last_maintenance, price, status)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
""", tools)
cnx.commit()
print("Inserted 200 tools.")

# ---------- Insert movements ----------
cursor.execute("SELECT id FROM employees")
employee_ids = [row[0] for row in cursor.fetchall()]
cursor.execute("SELECT id FROM tools")
tool_ids = [row[0] for row in cursor.fetchall()]

movements = []
for _ in range(100):  # simulate 100 movements
    tool_id = random.choice(tool_ids)
    employee_id = random.choice(employee_ids)
    date_emprunt = random_date(2023, 2025)
    expected_return = date_emprunt + timedelta(days=random.randint(1, 14))
    return_date = date_emprunt + timedelta(days=random.randint(1, 14)) if random.random() > 0.3 else None
    status = 'Returned' if return_date else 'Checked Out'
    movements.append((tool_id, employee_id, date_emprunt, expected_return, return_date, status))

cursor.executemany("""
    INSERT INTO movements
    (tool_id, employee_id, date_emprunt, expected_return, return_date, status)
    VALUES (%s,%s,%s,%s,%s,%s)
""", movements)
cnx.commit()
print("Inserted 100 movements.")

cursor.close()
cnx.close()
print("Database seeding complete.")
