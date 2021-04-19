import math

import requests
from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import abort, Api

from app.data.messages import Message
from app.data.orders import Order
from app.forms.message import MessageForm
from app.forms.search_user import UserSearchForm
from data import db_session
from data.offers import Offer
from data.users import User
from forms.offers import OfferForm
from forms.user import RegisterForm, LoginForm

app = Flask(__name__)
api = Api(app)
# run_with_ngrok(app)
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
def add_offer():
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


@app.route('/messages/<int:id_to>', methods=['GET', 'POST'])
@login_required
def add_message(id_to):
    form = MessageForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        message = Message()
        message.title = form.title.data
        message.content = form.content.data
        message.user_id_to = id_to
        message.user_id_from = current_user.id
        db_sess.add(message)
        db_sess.commit()
        return redirect(f'/messages_history/{id_to}')
    return render_template('messages.html', form=form)


def parse_the_date(date):
    ymd = date.split()[0]
    hms = date.split()[1]
    year = int(ymd.split("-")[0])
    month = int(ymd.split("-")[1])
    day = int(ymd.split("-")[2])
    hour = int(hms.split(":")[0])
    minute = int(hms.split(":")[1])
    second = int(hms.split(":")[2].split(".")[0])
    return [year, month, day, hour, minute, second]


@app.route('/messages_history/<int:id_to>')
@login_required
def message_history(id_to):
    db_sess = db_session.create_session()
    user_to = db_sess.query(User).filter((User.id == id_to)).first()
    messages = db_sess.query(Message).filter((Message.user_id_to == id_to) | (Message.user_id_to == current_user.id)).all()
    messages_users = []
    for message in messages:
        messages_users.append((message, db_sess.query(User).filter((User.id == message.user_id_from)).first(),  db_sess.query(User).filter((User.id == message.user_id_to)).first()))
    messages_users.sort(key=lambda mesg: parse_the_date(str(mesg[0].created_date)))
    db_sess.commit()
    return render_template("message_history.html", messages=messages_users, user_to=user_to, current_user=current_user)


@app.route('/orders_fulfilled/<int:id>/<int:offer_id>')
@login_required
def orders_fulfilled(id, offer_id):
    db_sess = db_session.create_session()
    offer = db_sess.query(Offer).filter(Offer.id == offer_id).first()
    if offer:
        offer.is_taken = False
        db_sess.commit()
    else:
        abort(404)
    order = db_sess.query(Order).filter(Order.id == id).first()
    if order:
        order.is_active = False
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route("/make_order/<int:id>")
@login_required
def make_order(id):
    if current_user.is_authenticated:
        # создаем заказ и помещаем его в БД
        order = Order()
        db_sess = db_session.create_session()
        order.offer_id = id
        # убираем предложение из списка не выбранных
        offer = db_sess.query(Offer).filter((Offer.id == id)).one()
        offer.is_taken = True
        order.user_id = current_user.id
        order.is_active = True
        db_sess.add(order)
        db_sess.commit()
        return redirect("/my_orders")
    else:
        abort(404)


@app.route("/orders_to_take")
@login_required
def orders_to_take():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        offers_id = db_sess.query(Offer.id).filter((Offer.user_id == current_user.id))
        orders = db_sess.query(Order).filter((Order.offer_id.in_(offers_id)), (Order.is_active == True))
    else:
        orders = db_sess.query(Order).filter(Order.is_active == True)
    db_sess.commit()
    return render_template("orders_to_take.html", orders=orders)


@app.route("/my_orders")
@login_required
def my_orders():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        orders = db_sess.query(Order).filter((Order.user_id == current_user.id), (Order.is_active == True))
    else:
        orders = db_sess.query(Order).filter(Order.is_active == True)
    db_sess.commit()
    return render_template("orders.html", orders=orders)


@app.route("/look_details/<int:offer_id>")
@login_required
def look_details(offer_id):
    db_sess = db_session.create_session()
    offer = db_sess.query(Offer).filter((Offer.id == offer_id), (Offer.is_taken == True)).first()
    title = offer.title
    id = offer.id
    user = offer.user
    date = offer.created_date
    content = offer.content
    db_sess.commit()
    return render_template("look_details.html", title=title, date=date, content=content, user=user, id=id)


@app.route('/orders_delete/<int:id>/<int:offer_id>')
@login_required
def orders_delete(id, offer_id):
    db_sess = db_session.create_session()
    offer = db_sess.query(Offer).filter(Offer.id == offer_id).first()
    if offer:
        offer.is_taken = False
        db_sess.commit()
    else:
        abort(404)
    order = db_sess.query(Order).filter(Order.id == id).first()
    if order:
        order.is_active = False
        db_sess.commit()
    else:
        abort(404)
    return redirect('/my_orders')


@app.route('/offers_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def offers_delete(id):
    db_sess = db_session.create_session()
    offers = db_sess.query(Offer).filter(Offer.id == id, Offer.user == current_user).first()
    if offers:
        db_sess.delete(offers)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/display_offers/<int:user_id>')
@login_required
def display_offers(user_id):
    db_sess = db_session.create_session()
    offers = db_sess.query(Offer).filter(Offer.user_id == user_id, Offer.is_taken == False).all()
    user = db_sess.query(User).filter((User.id == user_id)).first()
    db_sess.commit()
    return render_template("display_offers.html", offers=offers, user=user)


@app.route('/offers/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_offers(id):
    form = OfferForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        offer = db_sess.query(Offer).filter(Offer.id == id, Offer.user == current_user).first()
        if offer:
            form.title.data = offer.title
            form.content.data = offer.content

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        offer = db_sess.query(Offer).filter(Offer.id == id, Offer.user == current_user).first()
        if offer:
            offer.title = form.title.data
            offer.content = form.content.data
            db_sess.commit()
            return redirect('/')

    return render_template('offers.html', title='Редактирование предложения', form=form)


@app.route('/search_user', methods=['GET', 'POST'])
@login_required
def search_user():
    form = UserSearchForm()
    if request.method == "POST":
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            users = db_sess.query(User).filter(User.name.like(f'%{form.title.data}%'), User != current_user).all()
            db_sess.commit()
            if users:
                return render_template("search_user.html", users=users, message=f"Users found: {len(users)}", form=form)
            else:
                return render_template("search_user.html", users=None, message=f"Users found: 0", form=form)
        return redirect("/search_user")
    return render_template("search_user.html", users=None, message=f"enter the name", form=form)


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
            about=form.about.data,
            country=form.country.data,
            city=form.city.data,
            building=form.building.data,
            district=form.district.data
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


def calculate_distance_points(a, b):
    degree_to_meters_factor = 111 * 1000  # 111 километров в метрах
    a_lon, a_lat = float(a[0]), float(a[1])
    b_lon, b_lat = float(b[0]), float(b[1])
    # Берем среднюю по широте точку и считаем коэффициент для нее.
    radians_lattitude = math.radians((a_lat + b_lat) / 2.)
    lat_lon_factor = math.cos(radians_lattitude)
    # Вычисляем смещения в метрах по вертикали и горизонтали.
    dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
    dy = abs(a_lat - b_lat) * degree_to_meters_factor
    # Вычисляем расстояние между точками.
    distance = math.sqrt(dx * dx + dy * dy)
    return distance


def return_coors(name):
    toponym_to_find = name
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-9853"
                  "3de7710b",
        "geocode": toponym_to_find,
        "format": "json"}
    response = requests.get(geocoder_api_server, params=geocoder_params)
    if not response:
        return None
    # Преобразуем ответ в json-объект
    json_response = response.json()
    # Получаем первый топоним из ответа геокодера.
    toponym = json_response["response"]["GeoObjectCollection"][
        "featureMember"][0]["GeoObject"]
    # Координаты центра топонима:
    toponym_coodrinates = toponym["Point"]["pos"]
    # Долгота и широта:
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
    toponym_lattitude = float(toponym_lattitude)
    toponym_longitude = float(toponym_longitude)
    return (toponym_longitude, toponym_lattitude)


@app.route("/distance/<int:user_id>")
@login_required
def distance(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    address_to = f'{user.country},{user.city},{user.district},{user.building}'
    address_from = f'{current_user.country},{current_user.city},{current_user.district},{current_user.building}'
    print(address_from, address_to)
    coordinates_to = return_coors(address_to)
    coordinates_from = return_coors(address_from)
    distance_from_to = calculate_distance_points(coordinates_from, coordinates_to)
    delta = str(float(distance_from_to * 1.5 / 111134.861111))
    print(distance_from_to)
    center_lattitude = abs(coordinates_to[0] + coordinates_from[0]) / 2
    center_longitude = abs(coordinates_to[1] + coordinates_from[1]) / 2
    map_params = {
        "ll": ",".join([str(center_lattitude), str(center_longitude)]),
        "l": "map",
        "spn": ",".join([delta, delta]),
        "pt": f"{coordinates_to[0]},{coordinates_to[1]},pm2grl~{coordinates_from[0]},{coordinates_from[1]},pm2dgl",
        "pl": ",".join(
            [str(coordinates_to[0]), str(coordinates_to[1]), str(coordinates_from[0]), str(coordinates_from[1])]),

    }
    map_api_server = "http://static-maps.yandex.ru/1.x/"
    # ... и выполняем запрос
    response = requests.get(map_api_server, params=map_params)
    map_url = response.url
    print(map_url)
    return render_template("show_distance.html", map_url=map_url, user=user, address_to=address_to,
                           address_from=address_from, distance_from_to=int(distance_from_to), current_user=current_user)


if __name__ == '__main__':
    main()
