from flask import Flask,flash
from extension import db
from flask_login import LoginManager
from models import User,Expense
from forms import LoginForm,RegisterForm
from collections import defaultdict
import json

app = Flask(__name__)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

app.config["SECRET_KEY"]='246fa77f93c59959f05f8da2'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"

db.init_app(app)







#login route 
from flask import render_template, redirect, url_for, flash,abort
from flask_login import login_user
from werkzeug.security import check_password_hash,generate_password_hash

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html", form=form)
       



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



#register route 
@app.route("/register", methods=["GET", "POST"])
def register():
    form =RegisterForm()

    if form.validate_on_submit():
        print("Form validated")

        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()

        if existing_user:
            flash("Email already registered!", "danger")
            return redirect(url_for("register"))

        # Hash password
        hashed_password = generate_password_hash(form.password.data)

        # Create new user
        new_user = User(
            email=form.email.data,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)   

from flask_login import login_required, current_user


#expense route 
from flask import request
from flask_login import current_user

@app.route("/add_expense", methods=["POST"])
@login_required
def add_expense():
    amount = request.form.get("amount")
    category = request.form.get("category")
    description = request.form.get("description")

    if amount and category:
        new_expense = Expense(
            amount=float(amount),
            category=category,
            description=description,
            user_id=current_user.id
        )
        db.session.add(new_expense)
        db.session.commit()

    return redirect(url_for("dashboard"))

from flask_login import login_required, current_user,logout_user


@app.route("/logout")
@login_required
def logout():
    logout_user()  
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))


#dashboard route 
from collections import defaultdict
import json

@app.route("/dashboard")
@login_required
def dashboard():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()

    total = sum(exp.amount for exp in expenses)

    category_data = defaultdict(float)

    for exp in expenses:
        category_data[exp.category] += exp.amount

    labels = list(category_data.keys())
    values = list(category_data.values())

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total=total,
        labels=json.dumps(labels),
        values=json.dumps(values)
    ) 

#delete route 
@app.route("/delete_expense/<int:id>", methods=["POST"])
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)

    if expense.user_id != current_user.id:
        abort(403)

    db.session.delete(expense)
    db.session.commit()

    flash("Expense deleted successfully!", "info")
    return redirect(url_for("dashboard"))

#edit route 
@app.route("/edit_expense/<int:id>", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)

    # Security check
    if expense.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        expense.amount = float(request.form.get("amount"))
        expense.category = request.form.get("category")
        expense.description = request.form.get("description")

        db.session.commit()

        flash("Expense updated successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("editexpense.html", expense=expense)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

