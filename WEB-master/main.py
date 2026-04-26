import datetime
import os

from flask import Flask, request, render_template, redirect, abort, jsonify, session, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from data import db_session
from data.users import User
from data.news import News
from data.product import Product
from data.cart import CartItem
from data.favorite import Favorite
from data.order import Order, OrderItem
from data.advertisement import Advertisement
from forms.loginform import LoginForm
from forms.news import NewsForm
from forms.user import RegisterForm
from forms.profile import ProfileForm, PasswordChangeForm
from forms.product import ProductForm
from apis.users_api import users_api
from apis.news_api import news_api

app = Flask(__name__)
app.config["SECRET_KEY"] = "just_simple_key"
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=365)

login_manager = LoginManager()
login_manager.init_app(app)

os.makedirs("db", exist_ok=True)
db_session.global_init("db/blogs.sqlite")

app.register_blueprint(users_api)
app.register_blueprint(news_api)


def get_delivery_cost(total):
    if total >= 5000:
        return 0.0
    elif total >= 3000:
        return 200.0
    return 500.0


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.context_processor
def inject_cart_count():
    if current_user.is_authenticated:
        return {'cart_count': session.get('cart_count', 0)}
    return {'cart_count': 0}


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    return render_template("404.html"), 404


@app.route("/")
@app.route("/index")
def index():
    db_sess = db_session.create_session()
    promo_products = db_sess.query(Product).filter(Product.is_on_sale == True).limit(4).all()
    if not promo_products:
        promo_products = db_sess.query(Product).order_by(Product.created_date.desc()).limit(4).all()
    ads = db_sess.query(Advertisement).filter(Advertisement.is_active == True).all()
    return render_template("index.html",
                           title="Главная - ОфисМаркет",
                           user=current_user,
                           promo_products=promo_products,
                           ads=ads)


@app.route("/catalog")
def catalog():
    db_sess = db_session.create_session()
    query = db_sess.query(Product)

    search = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    sort = request.args.get('sort', '')

    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if category:
        query = query.filter(Product.category == category)
    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'sale':
        query = query.filter(Product.is_on_sale == True)
    else:
        query = query.order_by(Product.created_date.desc())

    products = query.all()
    all_products = db_sess.query(Product).all()
    categories = sorted(set(p.category for p in all_products if p.category))

    favorite_ids = set()
    if current_user.is_authenticated:
        favs = db_sess.query(Favorite).filter(Favorite.user_id == current_user.id).all()
        favorite_ids = {f.product_id for f in favs}

    return render_template("catalog.html",
                           title="Каталог товаров",
                           products=products,
                           categories=categories,
                           current_category=category,
                           current_search=search,
                           current_sort=sort,
                           favorite_ids=favorite_ids)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db_sess = db_session.create_session()
    product = db_sess.get(Product, product_id)
    if not product:
        abort(404)
    recommended = db_sess.query(Product).filter(
        Product.category == product.category,
        Product.id != product_id
    ).limit(3).all()
    is_favorite = False
    if current_user.is_authenticated:
        is_favorite = db_sess.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.product_id == product_id
        ).first() is not None
    return render_template("product_detail.html",
                           title=product.name,
                           product=product,
                           recommended=recommended,
                           is_favorite=is_favorite)


@app.route("/toggle_favorite/<int:product_id>")
@login_required
def toggle_favorite(product_id):
    db_sess = db_session.create_session()
    existing = db_sess.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.product_id == product_id
    ).first()
    if existing:
        db_sess.delete(existing)
    else:
        db_sess.add(Favorite(user_id=current_user.id, product_id=product_id))
    db_sess.commit()
    next_url = request.args.get('next', url_for('catalog'))
    return redirect(next_url)


@app.route("/favorites")
@login_required
def favorites():
    db_sess = db_session.create_session()
    favs = db_sess.query(Favorite).filter(Favorite.user_id == current_user.id).all()
    return render_template("favorites.html", title="Избранное", favorites=favs)


@app.route("/add_to_cart/<int:product_id>")
@login_required
def add_to_cart(product_id):
    db_sess = db_session.create_session()
    product = db_sess.get(Product, product_id)
    if not product:
        abort(404)
    cart_item = db_sess.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == product_id
    ).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        db_sess.add(CartItem(user_id=current_user.id, product_id=product_id, quantity=1))
    db_sess.commit()
    session['cart_count'] = db_sess.query(CartItem).filter(CartItem.user_id == current_user.id).count()
    return redirect(url_for('cart'))


@app.route("/cart")
@login_required
def cart():
    db_sess = db_session.create_session()
    cart_items = db_sess.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    delivery = get_delivery_cost(subtotal)
    total = subtotal + delivery
    return render_template("cart.html",
                           title="Корзина",
                           cart_items=cart_items,
                           subtotal=subtotal,
                           delivery=delivery,
                           total=total)


@app.route("/update_cart", methods=["POST"])
@login_required
def update_cart():
    db_sess = db_session.create_session()
    for key, value in request.form.items():
        if key.startswith('quantity_'):
            item_id = int(key.split('_')[1])
            quantity = int(value)
            cart_item = db_sess.get(CartItem, item_id)
            if cart_item and cart_item.user_id == current_user.id:
                if quantity > 0:
                    cart_item.quantity = quantity
                else:
                    db_sess.delete(cart_item)
    db_sess.commit()
    session['cart_count'] = db_sess.query(CartItem).filter(CartItem.user_id == current_user.id).count()
    return redirect(url_for('cart'))


@app.route("/remove_from_cart/<int:item_id>")
@login_required
def remove_from_cart(item_id):
    db_sess = db_session.create_session()
    cart_item = db_sess.get(CartItem, item_id)
    if cart_item and cart_item.user_id == current_user.id:
        db_sess.delete(cart_item)
        db_sess.commit()
        session['cart_count'] = db_sess.query(CartItem).filter(CartItem.user_id == current_user.id).count()
    return redirect(url_for('cart'))


@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    db_sess = db_session.create_session()
    cart_items = db_sess.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        return redirect(url_for('cart'))

    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    delivery = get_delivery_cost(subtotal)
    total = subtotal + delivery

    user = db_sess.get(User, current_user.id)
    if user.balance < total:
        return render_template("cart.html",
                               title="Корзина",
                               cart_items=cart_items,
                               subtotal=subtotal,
                               delivery=delivery,
                               total=total,
                               error="Недостаточно средств на балансе")

    order = Order(user_id=current_user.id, total_amount=subtotal,
                  delivery_cost=delivery, status='confirmed')
    db_sess.add(order)
    db_sess.flush()

    for item in cart_items:
        db_sess.add(OrderItem(order_id=order.id, product_id=item.product_id,
                              quantity=item.quantity, price=item.product.price))
        product = db_sess.get(Product, item.product_id)
        if product:
            product.stock = max(0, product.stock - item.quantity)
        db_sess.delete(item)

    user.balance -= total
    db_sess.commit()
    session['cart_count'] = 0
    return redirect(url_for('orders'))


@app.route("/orders")
@login_required
def orders():
    db_sess = db_session.create_session()
    user_orders = db_sess.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_date.desc()).all()
    return render_template("orders.html", title="Мои заказы", orders=user_orders)


@app.route("/seller/products")
@login_required
def seller_products():
    if current_user.user_type != 'seller':
        abort(403)
    db_sess = db_session.create_session()
    products = db_sess.query(Product).filter(Product.seller_id == current_user.id).all()
    return render_template("seller_products.html", title="Мои товары", products=products)


@app.route("/seller/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    if current_user.user_type != 'seller':
        abort(403)
    form = ProductForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            old_price=form.old_price.data,
            category=form.category.data,
            stock=form.stock.data,
            is_on_sale=form.is_on_sale.data,
            seller_id=current_user.id
        )
        db_sess.add(product)
        db_sess.commit()
        return redirect(url_for('seller_products'))
    return render_template("add_product.html", title="Добавить товар", form=form)


@app.route("/seller/edit_product/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    if current_user.user_type != 'seller':
        abort(403)
    db_sess = db_session.create_session()
    product = db_sess.get(Product, product_id)
    if not product or product.seller_id != current_user.id:
        abort(404)
    form = ProductForm()
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.old_price = form.old_price.data
        product.category = form.category.data
        product.stock = form.stock.data
        product.is_on_sale = form.is_on_sale.data
        db_sess.commit()
        return redirect(url_for('seller_products'))
    form.name.data = product.name
    form.description.data = product.description
    form.price.data = product.price
    form.old_price.data = product.old_price
    form.category.data = product.category
    form.stock.data = product.stock
    form.is_on_sale.data = product.is_on_sale
    return render_template("add_product.html", title="Редактировать товар", form=form, product=product)


@app.route("/seller/delete_product/<int:product_id>")
@login_required
def delete_product(product_id):
    if current_user.user_type != 'seller':
        abort(403)
    db_sess = db_session.create_session()
    product = db_sess.get(Product, product_id)
    if not product or product.seller_id != current_user.id:
        abort(404)
    db_sess.delete(product)
    db_sess.commit()
    return redirect(url_for('seller_products'))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()
    pwd_form = PasswordChangeForm()
    db_sess = db_session.create_session()
    user = db_sess.get(User, current_user.id)
    params = {"title": "Личный кабинет", "form": form, "pwd_form": pwd_form, "user": user}

    if 'submit' in request.form and form.validate_on_submit():
        if db_sess.query(User).filter(User.id != user.id, User.email == form.email.data).first():
            params["message"] = "Этот email уже занят"
        else:
            user.name = form.name.data
            user.email = form.email.data
            user.about = form.about.data
            db_sess.commit()
            return redirect(url_for('profile'))

    if 'submit_password' in request.form and pwd_form.validate_on_submit():
        if not user.check_password(pwd_form.old_password.data):
            params["pwd_error"] = "Неверный текущий пароль"
        elif pwd_form.new_password.data != pwd_form.new_password_again.data:
            params["pwd_error"] = "Новые пароли не совпадают"
        else:
            user.set_password(pwd_form.new_password.data)
            db_sess.commit()
            params["pwd_success"] = "Пароль успешно изменён"

    form.name.data = user.name
    form.email.data = user.email
    form.about.data = user.about
    return render_template("profile.html", **params)


@app.route("/archive")
def archive():
    db_sess = db_session.create_session()
    archived_products = db_sess.query(Product).filter(Product.stock == 0).all()
    return render_template("archive.html", title="Архив товаров", products=archived_products)


@app.route("/news")
def all_news():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        all_news_items = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private != True)
        ).all()
    else:
        all_news_items = db_sess.query(News).filter(News.is_private != True).all()
    return render_template("news.html", title="Новости", news=all_news_items)


@app.route("/news/<int:id>", methods=["GET", "POST"])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            news.created_date = datetime.datetime.now()
            db_sess.commit()
            return redirect("/news")
        else:
            abort(404)
    return render_template("add_news.html", title="Редактирование новости", form=form)


@app.route("/add_news", methods=["GET", "POST"])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News(title=form.title.data, content=form.content.data,
                    is_private=form.is_private.data)
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect("/news")
    return render_template("add_news.html", title="Добавление новости", form=form)


@app.route("/news_del/<int:id>")
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect("/news")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template("register.html", title="Регистрация",
                                   message="Пароли не совпадают", form=form)
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template("register.html", title="Регистрация",
                                   message="Такой пользователь уже есть", form=form)
        user = User(name=form.name.data, email=form.email.data,
                    about=form.about.data, user_type=form.user_type.data, balance=10000.0)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect("/login")
    return render_template("register.html", title="Регистрация", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            session['cart_count'] = db_sess.query(CartItem).filter(CartItem.user_id == user.id).count()
            return redirect("/catalog")
    return render_template("login.html", title="Авторизация", f=form)


@app.route("/logout")
@login_required
def logout():
    session.pop('cart_count', None)
    logout_user()
    return redirect("/index")


@app.route("/about")
def about():
    return render_template("about.html", title="О нас")


@app.route("/contacts", methods=["GET", "POST"])
def get_feedback():
    return render_template("contacts.html", title="Обратная связь")


def seed_db():
    db_sess = db_session.create_session()
    if db_sess.query(User).count() > 0:
        return

    seller = User(name="Магазин Электроники", email="seller@shop.com",
                  user_type="seller", balance=0.0)
    seller.set_password("seller123")
    db_sess.add(seller)

    buyer = User(name="Иван Петров", email="buyer@shop.com",
                 user_type="buyer", balance=25000.0)
    buyer.set_password("buyer123")
    db_sess.add(buyer)
    db_sess.flush()

    products = [
        Product(name="Смартфон XYZ Pro", description="Мощный смартфон с отличной камерой и большим экраном AMOLED",
                price=29999, old_price=34999, category="Электроника", stock=15,
                is_on_sale=True, seller_id=seller.id),
        Product(name="Ноутбук ProBook 15", description="Идеален для работы и учёбы, мощный процессор, 16 ГБ ОЗУ",
                price=59999, old_price=69999, category="Электроника", stock=8,
                is_on_sale=True, seller_id=seller.id),
        Product(name="Беспроводные наушники", description="Отличное качество звука, ANC, до 30 часов работы",
                price=4999, category="Аксессуары", stock=25, seller_id=seller.id),
        Product(name="Умные часы Series X", description="Фитнес-трекер, GPS, уведомления, ЭКГ",
                price=12999, old_price=15999, category="Электроника", stock=10,
                is_on_sale=True, seller_id=seller.id),
        Product(name="Python для начинающих", description="Лучший учебник по Python с практическими примерами",
                price=899, category="Книги", stock=45, seller_id=seller.id),
        Product(name="Кофеварка автоматическая", description="Эспрессо, капучино, американо — всё в одном",
                price=15999, category="Бытовая техника", stock=5, seller_id=seller.id),
        Product(name="Старый планшет", description="Устаревшая модель, снята с производства",
                price=9999, category="Электроника", stock=0, seller_id=seller.id),
    ]
    for p in products:
        db_sess.add(p)

    ads = [
        Advertisement(title="Скидка 30% на электронику!", text="Только до конца месяца — лучшие гаджеты по сниженным ценам.",
                      link="/catalog?category=Электроника&sort=sale", badge="ХИТ"),
        Advertisement(title="Бесплатная доставка от 5000₽", text="Заказывайте больше — экономьте на доставке.",
                      link="/catalog", badge="ВЫГОДА"),

    ]
    for ad in ads:
        db_sess.add(ad)

    db_sess.commit()


seed_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
