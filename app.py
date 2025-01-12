from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "secret_key"  # Secret key for flash messages

# Database connection and creation
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=""
)

cursor = db.cursor()

# Create the database if it doesn't exist
cursor.execute("CREATE DATABASE IF NOT EXISTS ALFC")
db.database = "ALFC"

# Create the fighters table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS fighters (
    fighter_id INT PRIMARY KEY,
    fighter_name VARCHAR(100),
    father_name VARCHAR(100),
    status ENUM('Paid', 'Not Paid'),
    registration_date DATE
)
""")

# Home page
@app.route("/")
def index():
    return render_template("index.html")

# Add fighter
@app.route("/add", methods=["GET", "POST"])
def add_fighter():
    if request.method == "POST":
        fighter_id = request.form["id"]
        name = request.form["name"]
        father_name = request.form["father_name"]
        status = request.form["status"]
        registration_date = request.form["registration_date"]

        query = """
        INSERT INTO fighters (fighter_id, fighter_name, father_name, status, registration_date)
        VALUES (%s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (fighter_id, name, father_name, status, registration_date))
            db.commit()
            flash("Fighter added successfully!", "success")
        except mysql.connector.IntegrityError:
            flash("Error: ID already exists or invalid data!", "error")

        return redirect(url_for("index"))

    return render_template("add_fighter.html")

# Edit fighter
@app.route("/edit", methods=["GET", "POST"])
def edit_fighter():
    fighter = None
    if request.method == "POST" and "search" in request.form:
        search_id = request.form.get("id")
        search_name = request.form.get("name")

        # Ensure that at least one search field is filled
        if not search_id and not search_name:
            flash("Please provide either ID or Name to search!", "error")
            return render_template("edit_fighter.html", fighter=None)

        query = "SELECT * FROM fighters WHERE fighter_id = %s OR fighter_name = %s"
        cursor.execute(query, (search_id, search_name))
        fighter = cursor.fetchone()

        if not fighter:
            flash("Fighter not found!", "error")
        else:
            return render_template("edit_fighter.html", fighter=fighter)

    if request.method == "POST" and "update" in request.form:
        try:
            fighter_id = request.form["id"]
            name = request.form["name"]
            father_name = request.form["father_name"]
            status = request.form["status"]
            registration_date = request.form["registration_date"]

            # Update the fighter record
            query = """
            UPDATE fighters
            SET fighter_name = %s, father_name = %s, status = %s, registration_date = %s
            WHERE fighter_id = %s
            """
            cursor.execute(query, (name, father_name, status, registration_date, fighter_id))
            db.commit()
            flash("Fighter updated successfully!", "success")
        except Exception as e:
            flash(f"Error updating fighter: {e}", "error")

        return redirect(url_for("index"))

    if request.method == "POST" and "delete" in request.form:
        try:
            fighter_id = request.form["id"]
            query = "DELETE FROM fighters WHERE fighter_id = %s"
            cursor.execute(query, (fighter_id,))
            db.commit()
            flash("Fighter deleted successfully!", "success")
        except Exception as e:
            flash(f"Error deleting fighter: {e}", "error")

        return redirect(url_for("index"))

    return render_template("edit_fighter.html", fighter=fighter)

# View fighters
@app.route("/view", methods=["GET", "POST"])
def view_fighters():
    query = "SELECT * FROM fighters"
    filters = []
    filter_values = []

    if request.method == "POST":
        search = request.form.get("search")
        status = request.form.get("status")

        if search:
            filters.append("(fighter_name LIKE %s OR fighter_id = %s)")
            filter_values.extend([f"%{search}%", search])

        if status and status != "All":
            filters.append("status = %s")
            filter_values.append(status)

    if filters:
        query += " WHERE " + " AND ".join(filters)

    cursor.execute(query, filter_values)
    fighters = cursor.fetchall()

    return render_template("view_fighters.html", fighters=fighters)

# Update fighters' status based on registration date
def update_fighter_status():
    query = "SELECT fighter_id, status, registration_date FROM fighters"
    cursor.execute(query)
    fighters = cursor.fetchall()

    for fighter in fighters:
        fighter_id, status, registration_date = fighter
        # Ensure registration_date is a datetime object (it may be in string format)
        if isinstance(registration_date, str):
            registration_date = datetime.strptime(registration_date, "%Y-%m-%d").date()
        
        # Check if status is "Paid" and if the registration date is older than 30 days
        if status == "Paid" and datetime.now().date() > registration_date + timedelta(days=30):
            query = """
            UPDATE fighters
            SET status = 'Not Paid'
            WHERE fighter_id = %s
            """
            cursor.execute(query, (fighter_id,))
            db.commit()

if __name__ == "__main__":
    update_fighter_status()  # Check and update fighter status on app startup
    app.run(debug=True)
