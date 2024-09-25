from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SubmitField, BooleanField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo
from authlib.integrations.flask_client import OAuth
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import os
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email Config
app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# Initialize extensions
mail = Mail(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)

    def generate_otp(self):
        import random
        self.otp = str(random.randint(100000, 999999))
        self.otp_expiry = datetime.utcnow() + timedelta(minutes=30)
        db.session.commit()
    
    def verify_otp(self, otp):
        if self.otp == otp and datetime.utcnow() < self.otp_expiry:
            self.otp = None
            self.otp_expiry = None
            self.confirmed = True
            db.session.commit()
            return True
        return False

# WasteData model
class WasteData(db.Model):
    __tablename__ = 'WasteData'  # Ensures case-sensitive table name
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    dry_waste = db.Column(db.Float, nullable=False, default=0)
    wet_waste = db.Column(db.Float, nullable=False, default=0)
    weight = db.Column(db.Float, nullable=False, default=0)

# Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ManualEntryForm(FlaskForm):
    dry_waste = FloatField('Dry Waste (kg)', validators=[DataRequired()])
    wet_waste = FloatField('Wet Waste (kg)', validators=[DataRequired()])
    weight = FloatField('Total Weight (kg)', validators=[DataRequired()])
    submit = SubmitField('Submit Data')

# Email Functions
def send_confirmation_email(user):
    token = user.generate_otp()
    msg = Message('Confirm Your Account', sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[user.email])
    msg.body = f'''To confirm your account, use the following OTP:
{token}

This OTP will expire in 30 minutes.'''
    mail.send(msg)
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    waste_data = WasteData.query.all()
    total_dry = sum(data.dry_waste for data in waste_data)
    total_wet = sum(data.wet_waste for data in waste_data)
    total_weight = sum(data.weight for data in waste_data)
    return render_template('dashboard.html', waste_data=waste_data, total_dry=total_dry, total_wet=total_wet, total_weight=total_weight)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        send_confirmation_email(new_user)  # Send OTP for email confirmation
        flash('Your account has been created! Please check your email for OTP to confirm your account.', 'success')
        return redirect(url_for('verify_otp', user_id=new_user.id))
    return render_template('register.html', form=form)

@app.route('/verify-otp/<int:user_id>', methods=['GET', 'POST'])
def verify_otp(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        otp = request.form.get('otp')
        if user.verify_otp(otp):
            login_user(user)
            flash('Your email has been confirmed!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid or expired OTP', 'danger')
    return render_template('verify_otp.html', user=user)

@app.route('/manual_entry', methods=['GET', 'POST'])
@login_required
def manual_entry():
    form = ManualEntryForm()
    if form.validate_on_submit():
        new_data = WasteData(dry_waste=form.dry_waste.data, wet_waste=form.wet_waste.data, weight=form.weight.data)
        db.session.add(new_data)
        db.session.commit()
        flash('Data added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('manual_entry.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Initialize database and run app
if __name__ == '__main__':
    app.run(debug=True)
