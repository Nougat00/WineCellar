from flask import Flask, render_template, url_for, redirect, abort
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_bcrypt import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask import jsonify, request

app = Flask(__name__)
app.config["DEBUG"] = True
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="freedb_WineCellar",
    password="n86gtpe&%zcWBGu",
    hostname="sql.freedb.tech",
    databasename="freedb_Winecellar",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.secret_key = 'DZIWKI'

db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class Produkt(db.Model):
    __tablename__ = "produkt"
    id = db.Column(db.Integer, primary_key=True)
    kod_produktu = db.Column(db.String(32), nullable=False)
    nazwa_produktu = db.Column(db.String(80), nullable=False)
    typ_produktu = db.Column(db.String(80))
    kraj_pochodzenia = db.Column(db.String(80))
    region = db.Column(db.String(80))
    rocznik = db.Column(db.String(80))
    szczep = db.Column(db.String(80))
    opis = db.Column(db.String(250))
    status = db.Column(db.Boolean())
    created_ts = db.Column(db.DateTime())
    valid_from_date = db.Column(db.DateTime())
    valid_to_date = db.Column(db.DateTime())


class Sklep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kod_sklepu = db.Column(db.String(10))
    kod_sieci = db.Column(db.String(10))
    nazwa = db.Column(db.String(50))
    email = db.Column(db.String(30))
    telefon = db.Column(db.String(12))
    data_otwarcia = db.Column(db.Date())
    status = db.Column(db.Boolean())
    data_rejestracji = db.Column(db.Date())
    valid_from_date = db.Column(db.Date())
    long = db.Column(db.String(20))
    lat = db.Column(db.String(20))


class Oferta_sklepu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sklep_id = db.Column(db.Integer, db.ForeignKey('sklep.id'))
    produkt_id = db.Column(db.Integer, db.ForeignKey('produkt.id'))
    status = db.Column(db.Boolean())
    data_wprowadzenia = db.Column(db.Date())
    liczba_sztuk = db.Column(db.Integer())


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class RegisterForm(FlaskForm):
    username = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/location')
def location_on_map():
    # Your Google Maps API key
    api_key = "AIzaSyBs7UtztlVDEZtUey4m--mY5-m9y-gR1NQ"
    # Location coordinates (latitude, longitude)
    location = "54.341330,18.569030"
    return render_template("location_map.html", api_key=api_key, location=location)


class School:
    def __init__(self, key, name, lat, lng):
        self.key = key
        self.name = name
        self.lat = lat
        self.lng = lng


schools = (
    School('hv', 'Happy Valley Elementary', 37.9045286, -122.1445772),
    School('stanley', 'Stanley Middle', 37.8884474, -122.1155922),
    School('wci', 'Walnut Creek Intermediate', 37.9093673, -122.0580063)
)
schools_by_key = {school.key: school for school in schools}


@app.route("/shools")
def main():
    return render_template('main.html', schools=schools)


@app.route("/<school_code>")
def show_school(school_code):
    school = schools_by_key.get(school_code)
    if school:
        return render_template('map.html', school=school)
    else:
        abort(404)


@app.route('/points')
def pointsFunc():
    points = [[37.7749, -122.4194], [37.788022, -122.399797], [37.7999, -122.4469]]
    return render_template('index.html', points=points)


@app.route('/get_points', methods=['GET'])
def get_points():
    points = [[37.7749, -122.4194], [37.788022, -122.399797], [37.7999, -122.4469]]
    return jsonify(points)


if __name__ == "__main__":
    app.run(debug=True)
