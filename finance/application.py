import os

from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Get num shares per stock
    q = "SELECT SUM(shares), symbol FROM transactions WHERE user_id = ? GROUP BY symbol"
    shares = db.execute(q, session["user_id"])

    # Track amount of money
    total = 0

    # Get portfolio data
    portfolio = []
    for s in shares:

        # Check if no shares currently owned
        if s["SUM(shares)"] == 0:
            continue

        data = lookup(s["symbol"])

        # Store data
        item = {}
        item["shares"] = s["SUM(shares)"]
        item["symbol"] = s["symbol"]
        item["price"] = data["price"]
        item["name"] = data["name"]
        item["total"] = item["price"] * item["shares"]

        # Update total
        total += item["total"]

        portfolio.append(item)

    # Get cash
    q = "SELECT cash FROM users WHERE id = ?"
    cash = db.execute(q, session["user_id"])[0]["cash"]

    # Record current amound of cash
    item = {}
    item["shares"] = ""
    item["symbol"] = "CASH"
    item["price"] = None
    item["name"] = ""
    item["total"] = cash
    portfolio.append(item)

    return render_template("index.html", shares=portfolio, total=(total + item["total"]))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":

        # Get symbol and information
        symbol = request.form.get("symbol").upper()
        data = lookup(symbol)

        # Get shares
        shares = request.form.get("shares")

        # Check if is valid decimal
        try:
            float(shares)
        except:
            return apology("Invalid shares")

        originalShares = float(shares)
        shares = int(float(shares))

        # Num shares must be positive
        if shares < 1:
            return apology("Invalid shares")

        # Num shares must be an int
        if originalShares - shares != 0:
            return apology("Invalid shares")

        # Check if symbol is valid
        if data == None:
            return apology("Invalid symbol")

        # Check if user has enough money
        q = "SELECT cash FROM users WHERE id = ?"
        cash = db.execute(q, session["user_id"])[0]["cash"]
        cost = data["price"] * shares
        if cash < cost:
            return apology("Not enough money")

        # Buy stock
        q = "UPDATE users SET cash = ? WHERE id = ?"
        db.execute(q, cash - cost, session["user_id"])

        # Record transaction
        q = "INSERT INTO transactions (user_id, symbol, shares, price, time) VALUES (?, ?, ?, ?, ?)"
        db.execute(q, session["user_id"], symbol, shares, data["price"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Get transactions
    q = "SELECT * FROM transactions WHERE user_id = ?"
    transactions = db.execute(q, session["user_id"])

    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":

        # Get symbol and information
        symbol = request.form.get("symbol")
        data = lookup(symbol)

        # Invalid symbol
        if data == None:
            return apology("Invalid symbol")

        return render_template("quoted.html", data=data)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # Get form data
        name = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check if username is blank
        if len(name) == 0:
            return apology("Username is blank")

        # Check if username in use
        q = "SELECT username FROM users WHERE username = ?"
        usernames = db.execute(q, name)
        if len(usernames) > 0:
            return apology("Username in use")

        # Check if password is blank
        if len(password) == 0:
            return apology("Password is blank")

        # Check if password and confirmation match
        if password != confirmation:
            return apology("Passwords do not match")

        # If no errors create account and go to login
        q = "INSERT INTO users (username, hash) VALUES (?, ?)"
        db.execute(q, name, generate_password_hash(password))
        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":

        # Get symbol and information
        symbol = request.form.get("symbol").upper()
        data = lookup(symbol)

        # Get shares
        shares = request.form.get("shares")

        # Check if is valid decimal
        try:
            float(shares)
        except:
            return apology("Invalid shares")

        originalShares = float(shares)
        shares = int(float(shares))

        # Num shares must be positive
        if shares < 1:
            return apology("Invalid shares")

        # Num shares must be an int
        if originalShares - shares != 0:
            return apology("Invalid shares")

        # Check if symbol is valid
        if data == None:
            return apology("Invalid symbol")

        # Get num shares owned of stock
        q = "SELECT SUM(shares) FROM transactions WHERE user_id = ? AND symbol = ?"
        sharesOwned = db.execute(q, session["user_id"], symbol)

        # Check if stock owned
        if len(sharesOwned) == 0:
            return apology("Stock not owned")

        # Check if enough shares
        sharesOwned = sharesOwned[0]["SUM(shares)"]
        if sharesOwned < shares:
            return apology("Too many shares")

        # Sell stock
        # Get current cash
        q = "SELECT cash FROM users WHERE id = ?"
        cash = db.execute(q, session["user_id"])[0]["cash"]
        # Update cash
        q = "UPDATE users SET cash = ? WHERE id = ?"
        db.execute(q, cash + data["price"] * shares, session["user_id"])

        # Record transaction
        q = "INSERT INTO transactions (user_id, symbol, shares, price, time) VALUES (?, ?, ?, ?, ?)"
        db.execute(q, session["user_id"], symbol, -1 * shares, data["price"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return redirect("/")

    else:

        # Get stocks owned
        q = "SELECT SUM(shares), symbol FROM transactions WHERE user_id = ? GROUP BY symbol"
        stocks = db.execute(q, session["user_id"])
        stocks = [stock["symbol"] for stock in stocks if stock["SUM(shares)"] != 0]

        return render_template("sell.html", options=stocks)


@app.route("/money", methods=["GET", "POST"])
@login_required
def money():
    """Sell shares of stock"""

    if request.method == "POST":

        # Get shares
        amount = request.form.get("amount")

        # Check if is valid decimal
        try:
            amount = float(amount)
        except:
            return apology("Invalid amount")

        # Amount must be positive
        if amount < 1:
            return apology("Invalid amount")

        # Add amount to cash
        # Get current cash
        q = "SELECT cash FROM users WHERE id = ?"
        cash = db.execute(q, session["user_id"])[0]["cash"]
        # Update cash
        q = "UPDATE users SET cash = ? WHERE id = ?"
        db.execute(q, cash + amount, session["user_id"])

        return redirect("/")

    else:

        # Get current cash
        q = "SELECT cash FROM users WHERE id = ?"
        cash = db.execute(q, session["user_id"])[0]["cash"]

        return render_template("money.html", cash=cash)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
