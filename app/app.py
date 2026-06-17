"""
EcoChain Exchange - Carbon Credit Trading Platform
A small business application demonstrating the core domain for
Case Study 74: Global Carbon Credit Exchange Platform.

Run locally:
    pip install -r requirements.txt
    python app.py

Environment variables:
    DATABASE_URL  - SQLAlchemy DB URI (defaults to local sqlite file)
    SECRET_KEY    - Flask session secret
"""

import os
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from prometheus_flask_exporter import PrometheusMetrics

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///ecochain.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Prometheus metrics exposed at /metrics
metrics = PrometheusMetrics(app)
metrics.info("ecochain_app_info", "EcoChain Exchange application info", version="1.0.0")

login_manager = LoginManager(app)
login_manager.login_view = "login"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    organization = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="member")  # member | admin
    carbon_balance = db.Column(db.Float, default=0.0)  # tCO2e credits held
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class CreditListing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    credit_type = db.Column(db.String(50), nullable=False)  # Renewable, Forestry, etc.
    quantity = db.Column(db.Float, nullable=False)  # tCO2e
    price_per_credit = db.Column(db.Float, nullable=False)  # USD
    status = db.Column(db.String(20), default="active")  # active | sold | cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    seller = db.relationship("User")


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("credit_listing.id"))
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    credit_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    buyer = db.relationship("User", foreign_keys=[buyer_id])
    seller = db.relationship("User", foreign_keys=[seller_id])


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Routes - Auth
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        organization = request.form["organization"].strip()
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        user = User(username=username, organization=organization)
        user.set_password(password)
        # First user becomes the compliance admin
        if User.query.count() == 0:
            user.role = "admin"
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Routes - Core application
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    recent_tx = (
        Transaction.query.filter(
            (Transaction.buyer_id == current_user.id)
            | (Transaction.seller_id == current_user.id)
        )
        .order_by(Transaction.timestamp.desc())
        .limit(5)
        .all()
    )
    total_credits_traded = db.session.query(
        db.func.coalesce(db.func.sum(Transaction.quantity), 0)
    ).scalar()
    active_listings = CreditListing.query.filter_by(status="active").count()

    return render_template(
        "dashboard.html",
        recent_tx=recent_tx,
        total_credits_traded=total_credits_traded,
        active_listings=active_listings,
    )


@app.route("/marketplace")
@login_required
def marketplace():
    listings = CreditListing.query.filter_by(status="active").order_by(
        CreditListing.created_at.desc()
    ).all()
    return render_template("marketplace.html", listings=listings)


@app.route("/listing/create", methods=["GET", "POST"])
@login_required
def create_listing():
    if request.method == "POST":
        credit_type = request.form["credit_type"]
        quantity = float(request.form["quantity"])
        price = float(request.form["price"])

        if quantity <= 0 or price <= 0:
            flash("Quantity and price must be positive.", "danger")
            return redirect(url_for("create_listing"))

        listing = CreditListing(
            seller_id=current_user.id,
            credit_type=credit_type,
            quantity=quantity,
            price_per_credit=price,
        )
        db.session.add(listing)
        db.session.commit()
        flash("Carbon credit listing created.", "success")
        return redirect(url_for("marketplace"))

    return render_template("create_listing.html")


@app.route("/listing/<int:listing_id>/buy", methods=["POST"])
@login_required
def buy_listing(listing_id):
    listing = CreditListing.query.get_or_404(listing_id)

    if listing.status != "active":
        flash("This listing is no longer available.", "danger")
        return redirect(url_for("marketplace"))

    if listing.seller_id == current_user.id:
        flash("You cannot purchase your own listing.", "danger")
        return redirect(url_for("marketplace"))

    total_price = listing.quantity * listing.price_per_credit

    # Record transaction (simplified - no real payment gateway)
    tx = Transaction(
        listing_id=listing.id,
        buyer_id=current_user.id,
        seller_id=listing.seller_id,
        credit_type=listing.credit_type,
        quantity=listing.quantity,
        total_price=total_price,
    )
    current_user.carbon_balance += listing.quantity
    listing.status = "sold"

    db.session.add(tx)
    db.session.commit()

    flash(
        f"Purchased {listing.quantity} tCO2e of {listing.credit_type} credits.",
        "success",
    )
    return redirect(url_for("marketplace"))


@app.route("/transactions")
@login_required
def transactions():
    tx_list = (
        Transaction.query.filter(
            (Transaction.buyer_id == current_user.id)
            | (Transaction.seller_id == current_user.id)
        )
        .order_by(Transaction.timestamp.desc())
        .all()
    )
    return render_template("transactions.html", tx_list=tx_list)


@app.route("/admin")
@login_required
def admin():
    if current_user.role != "admin":
        flash("Access restricted to compliance administrators.", "danger")
        return redirect(url_for("dashboard"))

    all_tx = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    all_users = User.query.all()
    return render_template("admin.html", all_tx=all_tx, all_users=all_users)


# ---------------------------------------------------------------------------
# Routes - Operational endpoints (used by Docker/K8s/monitoring)
# ---------------------------------------------------------------------------
@app.route("/health")
def health():
    """Liveness/readiness probe endpoint for Docker & Kubernetes."""
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "up"
    except Exception:
        db_status = "down"

    return jsonify(status="ok", database=db_status, time=datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# CLI helper - initialise database
# ---------------------------------------------------------------------------
@app.cli.command("init-db")
def init_db():
    """Create database tables: `flask --app app init-db`"""
    db.create_all()
    print("Database tables created.")


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
