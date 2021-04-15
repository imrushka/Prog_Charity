from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from forms.offers import OfferForm
from forms.user import RegisterForm, LoginForm
from data.offers import Offer
from data.users import User
from data import db_session

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/charity.db")
    app.run(debug=True)


@app.route('/offers', methods=['GET', 'POST'])
@login_required
def add_news():
    form = OfferForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        offer = Offer()
        offer.title = form.title.data
        offer.content = form.content.data
        offer.is_taken = False
        current_user.offers.append(offer)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('offers.html', title='Добавление предложения', form=form)


@app.route('/offers_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    offers = db_sess.query(Offer).filter(Offer.id == id, Offer.user == current_user).first()
    if offers:
        db_sess.delete(offers)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/offers/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = OfferForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        offer = db_sess.query(Offer).filter(Offer.id == id, Offer.user == current_user).first()
        if offer:
            form.title.data = offer.title
            form.content.data = offer.content
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        offer = db_sess.query(Offer).filter(Offer.id == id, Offer.user == current_user).first()
        if offer:
            offer.title = form.title.data
            offer.content = form.content.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('offers.html', title='Редактирование предложения', form=form)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        offers = db_sess.query(Offer).filter((Offer.user == current_user) | (Offer.is_taken != True))
    else:
        offers = db_sess.query(Offer).filter(Offer.is_taken != True)
    return render_template("index.html", offers=offers)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


if __name__ == '__main__':
    main()
