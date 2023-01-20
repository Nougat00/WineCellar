from flask import Flask, render_template, url_for, redirect, abort, flash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from flask_wtf import FlaskForm
from flask_bcrypt import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask import jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["DEBUG"] = True
server = "winecellar.mysql.database.azure.com"
database = "mysql"
username = "winecellar"
password = "Dupsko1234"

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://winecellar:Dupsko1234@winecellar.mysql.database.azure.com/winecellar"
app.config['SECRET_KEY'] = 'supersecret'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# extensions
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
    szer_geogr = db.Column(db.Numeric(12, 9))
    dl_geogr = db.Column(db.Numeric(12, 9))


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
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Nazwa użytkownika"})

    password = PasswordField(validators=[
        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Hasło"})

    submit = SubmitField('Zarejestruj się')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
        InputRequired(), Length(min=0, max=20)], render_kw={"placeholder": "Nazwa użytkownika"})

    password = PasswordField(validators=[
        InputRequired(), Length(min=0, max=20)], render_kw={"placeholder": "Hasło"})

    submit = SubmitField('Zaloguj się')


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
            else:
                flash("Nieprawidłowy login lub hasło", "warning")
        else:
            flash("Nieprawidłowy login lub hasło", "warning")
    return render_template('login.html', form=form)


@app.route('/dashboard')
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
    else:
        flash("Wybrana nazwa użytkownika jest już zajęta", "warning")
    return render_template('register.html', form=form)


@app.route('/location')
def location_on_map():
    # Your Google Maps API key
    api_key = "AIzaSyBs7UtztlVDEZtUey4m--mY5-m9y-gR1NQ"
    # Location coordinates (latitude, longitude)
    location = "54.341330,18.569030"
    return render_template("location_map.html", api_key=api_key, location=location)


@app.route("/shops")
def shops():
    shops = Sklep.query.all()
    return render_template('shops.html', shops=shops)


@app.route("/shops/<kod_sklepu>")
def show_shop(kod_sklepu):
    shops = Sklep.query.all()
    shops_by_key = {shop.kod_sklepu: shop for shop in shops}
    shop = shops_by_key.get(kod_sklepu)
    result = db.engine.execute("select pr.nazwa_produktu, os.liczba_sztuk, pr.typ_produktu, pr.kraj_pochodzenia, pr.region, pr.rocznik, pr.szczep, pr.opis from produkt pr join oferta_sklepu os on pr.id = os.produkt_id join sklep sk on os.sklep_id = sk.id where os.liczba_sztuk > 0 and kod_sklepu = '"+kod_sklepu+"'")
    products = [row for row in result]
    print(products)
    if shop:
        return render_template('map.html', shop=shop, products=products)
    else:
        abort(404)


@app.route("/wines")
def wines():
    products = Produkt.query.all()
    return render_template('wines.html', products=products)


@app.route("/wines/<kod_produktu>")
def show_product(kod_produktu):
    products = Produkt.query.all()
    products_by_key = {product.kod_produktu: product for product in products}
    product = products_by_key.get(kod_produktu)
    if product:
        return render_template('product.html', product=product)
    else:
        abort(404)


if __name__ == "__main__":
    app.run(debug=True)
