import datetime
import io
import os
from decimal import Decimal
from sys import prefix

from flask import (
    Flask,
    request,
    render_template,
    redirect,
    abort,
    jsonify,
    session,
    url_for, send_file)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)

from data import db_session
from data.advertisement import Advertisement
from data.favorite import Favorite
from data.news import News
from data.order import Order, OrderItem
from data.users import User
from data.product import Product, ProductImages
from data.cart import CartItem
from forms.loginform import LoginForm
from forms.news import NewsForm
from forms.password_change_profile import PasswordChangeForm
from forms.user import RegisterForm
from forms.profile import ProfileForm
from forms.product import ProductForm
from forms.add_money import AddMoneyForm
from forms.submit_form import SubmitBuyForm
from forms.catalog_sort import CatalogSortForm
from forms.catalog_del import CatalogDelProdForm
# для добавления APIs
from apis.users_api import users_api
from apis.news_api import news_api
# for images
from PIL import Image
# for decorators
from custom_decorators import for_sellers

app = Flask(__name__)
app.config["SECRET_KEY"] = "just_simple_key"
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=365)
ADMIN_EMAIL = "1@mail.ru"

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    temp = db_sess.get(User, user_id)
    return temp


@app.teardown_appcontext
def shut_sess(exception=None):
    db_session.create_session().remove()


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):  # если это API — возвращаем JSON
        return jsonify({
            "error": "Not found"
        }), 404
    # иначе обычная страница
    return render_template("404.html"), 404


@app.errorhandler(403)
def access_forbidden(error):
    if request.path.startswith("/api/"):  # если это API — возвращаем JSON
        return jsonify({
            "error": "Access forbidden"
        }), 403
    # иначе обычная страница
    return render_template("403.html"), 403

@app.errorhandler(401)
def unauthorized_access(error):
    if request.path.startswith("/api/"):  # если это API — возвращаем JSON
        return jsonify({
            "error": "Unauthorized access"
        }), 401
    # иначе обычная страница
    return render_template("401.html"), 401


@app.route("/")  # декоратор
@app.route("/index")
def index():
    # Получаем товары для рекламы (последние 4 товара со скидкой или новинки)
    db_sess = db_session.create_session()
    promo_products = db_sess.query(Product).filter(
        Product.is_on_sale == True
    ).limit(4).all()

    if not promo_products:
        promo_products = db_sess.query(Product).order_by(
            Product.created_date.desc()
        ).limit(4).all()
    ads = db_sess.query(Advertisement).filter(
        Advertisement.is_active == True).all()
    params = {"current_user": current_user,
              "title": "Главная - Магазин",
              "promo_products": promo_products, "ads": ads}
    return render_template("index.html", **params)


@app.route("/catalog", methods=["GET", "POST"])
def catalog():
    sort_form = CatalogSortForm(prefix="a")
    del_form = CatalogDelProdForm(prefix="b")
    db_sess = db_session.create_session()
    products = db_sess.query(Product).order_by(Product.price)
    return catalog_similar(sort_form=sort_form, del_form=del_form,
                           products=products, db_sess=db_sess, title="Товары")


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db_sess = db_session.create_session()
    product = db_sess.get(Product, product_id)
    if not product:
        abort(404)
    recommended = db_sess.query(Product).filter(  # Рекомендуемые товары (из той же категории)
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
                           recommended=recommended, url_for=url_for, is_favorite=is_favorite)


@app.route("/product_img/<int:product_id>")
def product_img(product_id):
    db_sess = db_session.create_session()
    img = db_sess.query(ProductImages).filter(
        ProductImages.product_id == product_id).first()
    return send_file(io.BytesIO(img.image), mimetype="image/jpeg")


@app.route("/add_to_cart/<int:product_id>")
@login_required
def add_to_cart(product_id):
    db_sess = db_session.create_session()
    product = db_sess.get(Product, product_id)

    if not product:
        abort(404)

    cart_item = db_sess.query(CartItem).filter(   # Проверяем, есть ли уже этот товар в корзине
        CartItem.user_id == current_user.id,
        CartItem.product_id == product_id
    ).first()

    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=1
        )
        db_sess.add(cart_item)
    cart_count = db_sess.query(CartItem).filter(   # Сохраняем количество товаров в корзине в сессию
        CartItem.user_id == current_user.id
    ).count()
    db_sess.commit()

    session['cart_count'] = cart_count
    return redirect(url_for('cart'))


def get_delivery_cost(total):
    if total >= 5000:
        return 0.0
    elif total >= 3000:
        return 200.0
    return 500.0


def check_cart_counts():
    db_sess = db_session.create_session()
    for item in current_user.cart_items:
        if item.quantity > item.product.stock:
            if item.product.stock == 0:
                db_sess.delete(item)
            else:
                item.quantity = item.product.stock
    db_sess.commit()


@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    params = {"title": "Корзина"}
    form = SubmitBuyForm(prefix="a")
    check_cart_counts()
    db_sess = db_session.create_session()
    if form.validate_on_submit() and form.submit.data:
        summ = Decimal("0")
        for item in current_user.cart_items:
            summ += item.quantity * item.product.price
        if summ <= current_user.money:
            current_user.money -= summ
            new_order = Order(
                user_id=current_user.id,
                delivery_cost=get_delivery_cost(summ))
            for item in current_user.cart_items:
                item.user.money += item.quantity * item.product.price
                item.product.stock -= item.quantity
                new_order.items.append(OrderItem(product_id=item.product.id, quantity=item.quantity,
                                                 price=item.product.price))
                db_sess.delete(item)
            db_sess.add(new_order)
            params["message"] = "Покупка совершена успешно"
            update_cart()
        else:
            params["message"] = "На балансе недостаточно денег для покупки"
    cart_items = current_user.cart_items
    session['cart_count'] = len(cart_items)
    total = sum(item.product.price * item.quantity for item in cart_items)
    db_sess.commit()
    return render_template("cart.html",
                           cart_items=cart_items,
                           total=total, form=form, **params)


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
    cart_count = db_sess.query(CartItem).filter(
        # Обновляем счетчик корзины
        CartItem.user_id == current_user.id
    ).count()
    db_sess.commit()
    session['cart_count'] = cart_count
    return redirect(url_for('cart'))


@app.route("/remove_from_cart/<int:item_id>")
@login_required
def remove_from_cart(item_id):
    db_sess = db_session.create_session()
    cart_item = db_sess.get(CartItem, item_id)
    if cart_item and cart_item.user_id == current_user.id:
        db_sess.delete(cart_item)
        # Обновляем счетчик корзины
        cart_count = db_sess.query(CartItem).filter(
            CartItem.user_id == current_user.id
        ).count()
        session['cart_count'] = cart_count
    db_sess.commit()
    return redirect(url_for('cart'))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(prefix="a")
    pwd_form = PasswordChangeForm(prefix="b")
    db_sess = db_session.create_session()
    user = db_sess.get(User, current_user.id)
    params = {"title": "Личный кабинет", "form": form, "user": user, "money": str(float(user.money)),
              "pass_form": pwd_form}
    if 'submit_a' in request.form and form.validate_on_submit():
        if db_sess.query(User).filter(User.id != user.id,
                                      User.email == form.email.data).first():
            params["message"] = "Этот email уже занят"
        else:
            user.name = form.name.data
            user.email = form.email.data
            user.about = form.about.data
            db_sess.commit()
            return redirect(url_for('profile'))

    if 'submit_b' in request.form and pwd_form.validate_on_submit():
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
    favs = db_sess.query(Favorite).filter(
        Favorite.user_id == current_user.id).all()
    return render_template("favorites.html", title="Избранное", favorites=favs)


@app.route("/orders")
@login_required
def orders():
    db_sess = db_session.create_session()
    user_orders = db_sess.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_date.desc()).all()
    return render_template(
        "orders.html", title="Мои заказы", orders=user_orders)


def catalog_similar(sort_form, del_form, products, db_sess, title):
    if current_user.is_authenticated and del_form.validate_on_submit() and del_form.submit.data:
        to_del = db_sess.query(Product).filter(Product.id == int(del_form.product_id.data),
                                               Product.user_id == current_user.id).first()
        if to_del is not None:
            to_del.stock = 0
            db_sess.commit()
        else:
            abort(404)
    sort_form_full = False
    if sort_form.validate_on_submit() and sort_form.submit.data:
        if sort_form.min_price.data is None:
            prod = products.first()
            if prod is not None:
                sort_form.min_price.data = prod.price
        else:
            sort_form_full = True
        if sort_form.max_price.data is None:
            prod = products.all()
            if prod:
                sort_form.max_price.data = prod[-1].price
        else:
            sort_form_full = True
        print(sort_form.min_price.data, sort_form.max_price.data)
        products = products.filter(sort_form.max_price.data >= Product.price,
                                   Product.price >= sort_form.min_price.data).all()
        if sort_form.price.data == ">":
            products.reverse()
    else:
        products = products.all()
        if products:
            sort_form.min_price.data = products[0].price
            sort_form.max_price.data = products[-1].price
    favorite_ids = set()
    if current_user.is_authenticated:
        favs = db_sess.query(Favorite).filter(
            Favorite.user_id == current_user.id).all()
        favorite_ids = {f.product_id for f in favs}
    category = request.args.get('category')  # Фильтрация по категории
    search = request.args.get('search', '').strip()
    sale = request.args.get("sale")
    if category:
        products = [p for p in products if p.category == category]
    if search:
        products = [p for p in products if search.lower() in p.name.lower()]
    if sale == "T":
        products = [p for p in products if p.is_on_sale]
    # Получаем уникальные категории
    categories = list(set([p.category for p in products if p.category]))
    return render_template("catalog.html",
                           title=title,
                           products=products, current_search=search,
                           categories=categories,
                           current_category=category, sort_form=sort_form, del_form=del_form, str=str,
                           favorite_ids=favorite_ids, sale_sort=sale, sort_form_full=sort_form_full)


@app.route("/my_products", methods=["GET", "POST"])
@login_required
@for_sellers
def my_products():
    form_sort = CatalogSortForm(prefix="a")
    form_del = CatalogDelProdForm(prefix="b")
    db_sess = db_session.create_session()
    products = db_sess.query(Product).order_by(
        Product.price).filter(
        Product.user_id == current_user.id)
    return catalog_similar(sort_form=form_sort, del_form=form_del,
                           products=products, db_sess=db_sess, title="Мои товары")


@app.route("/selling_management")
@login_required
@for_sellers
def selling_management():
    return render_template("selling_management.html",
                           title="Продажи", money=str(float(current_user.money)))


def add_edit_product(edit=tuple()):
    db_sess = db_session.create_session()
    form = ProductForm()
    if form.validate_on_submit():
        if edit:
            product = db_sess.query(Product).filter(Product.id == edit[0],
                                                    Product.user_id == current_user.id).first()
            if product is None:
                abort(404)
        else:
            product = Product()
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.old_price = form.old_price.data
        product.category = form.category.data
        product.stock = form.stock.data
        product.is_on_sale = form.is_on_sale.data
        product.user_id = current_user.id
        img = Image.open(form.image.data)
        img.thumbnail((400, 400))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        if edit:
            db_sess.query(ProductImages).filter(ProductImages.product_id
                                                == product.id).first().image = buffer.getvalue()
        else:
            new_prod_img = ProductImages(product_id=get_future_product_id(),
                                         image=buffer.getvalue())
            db_sess.add(product)
            db_sess.add(new_prod_img)
        db_sess.commit()
        return redirect(url_for('catalog'))
    elif edit:
        product = db_sess.query(Product).filter(
            Product.id == edit[0],
            Product.user_id == current_user.id).first()
        if product is not None:
            form.name.data = product.name
            form.description.data = product.description
            form.price.data = product.price
            form.old_price.data = product.old_price
            form.category.data = product.category
            form.stock.data = product.stock
            form.is_on_sale.data = product.is_on_sale
        else:
            abort(404)
    return render_template("add_product.html",
                           title="Добавить товар",
                           form=form)


@app.route("/add_product", methods=["GET", "POST"])
@login_required
@for_sellers
def add_product():
    return add_edit_product()


@app.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
@login_required
@for_sellers
def edit_product(product_id):
    return add_edit_product((product_id, ))


def get_future_product_id():
    db_sess = db_session.create_session()
    temp = db_sess.query(Product).order_by(Product.id.desc()).first()
    if temp is not None:
        return temp.id + 1
    return 1


@app.route("/archive")
def archive():
    db_sess = db_session.create_session()
    # Архив - товары, которых нет в наличии
    archived_products = db_sess.query(Product).filter(Product.stock == 0).all()

    return render_template("archive.html",
                           title="Архив товаров",
                           products=archived_products)


@app.route("/news")
def all_news():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        all_news = (
            db_sess.query(News)
            .filter((News.user == current_user) | (News.is_private != True))
            .all()
        )
    else:
        all_news = db_sess.query(News).filter(News.is_private != True).all()

    return render_template("news.html", title="Список новостей", news=all_news)


@app.route("/news/<int:id>", methods=["GET", "POST"])
@login_required
def edit_news(id):
    form = NewsForm()
    db_sess = db_session.create_session()
    if request.method == "GET":
        news = (
            db_sess.query(News).filter(
                News.id == id, News.user == current_user).first()
        )
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = (
            db_sess.query(News).filter(
                News.id == id, News.user == current_user).first()
        )
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            news.created_date = datetime.datetime.now()
            db_sess.commit()
            return redirect("/news")
        else:
            abort(404)
    return render_template(
        "add_news.html", title="Редактирование новости", form=form)


@app.route("/add_news", methods=["GET", "POST"])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect("/news")
    return render_template(
        "add_news.html", title="Добавление новости", form=form)


@app.route("/news_del/<int:id>")
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(
        News.id == id, News.user == current_user).first()
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
            return render_template(
                "register.html",
                title="Пароли не совпали",
                message="Пароли не совпадают",
                form=form,
            )
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template(
                "register.html",
                title="Пользователь существует",
                message="Такой пользователь уже есть в базе",
                form=form,
            )
        user = User(
            name=form.name.data, email=form.email.data, about=form.about.data, is_seller=form.is_seller.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        return redirect("/login")
    return render_template("register.html", title="Регистрация", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    params = dict()
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            # Инициализируем корзину при входе
            cart_count = db_sess.query(CartItem).filter(
                CartItem.user_id == user.id
            ).count()
            session['cart_count'] = cart_count

            return redirect("/catalog")
        params["message"] = "Неправильный пароль или почта"

    return render_template("login.html", title="Авторизация", f=form, **params)


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


# Контекстный процессор для доступа к счетчику корзины во всех шаблонах
@app.context_processor
def inject_cart_count():
    if current_user.is_authenticated:
        return {'cart_count': session.get('cart_count', 0)}
    return {'cart_count': 0}


@app.route("/add_money", methods=["GET", "POST"])
def add_money():
    if current_user.is_authenticated and current_user.email == ADMIN_EMAIL:
        form = AddMoneyForm()
        params = {"title": "Money adding"}
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            redacted_user = db_sess.query(User).filter(
                form.email.data == User.email).first()
            if redacted_user is not None:
                redacted_user.money += form.money.data
                db_sess.commit()
                return "Success"
            params["message"] = "This user is not exist"
        return render_template("admin_panel.html", **params, form=form)


def ads():
    db_sess = db_session.create_session()
    if not db_sess.query(Advertisement).all():
        ads = [
            Advertisement(title="Скидка 30% на электронику!",
                      text="Только до конца месяца — лучшие гаджеты по сниженным ценам.",
                      link="/catalog?category=Электроника&sort=sale", badge="ХИТ"),
            Advertisement(title="Бесплатная доставка от 5000₽", text="Заказывайте больше — экономьте на доставке.",
                      link="/catalog", badge="ВЫГОДА"),
        ]
        for ad in ads:
            db_sess.add(ad)
        db_sess.commit()


if __name__ == "__main__":
    # Создаем папку для базы данных если её нет
    if not os.path.exists("db"):
        os.makedirs("db")
    db_session.global_init("db/blogs.sqlite")
    app.register_blueprint(users_api)
    app.register_blueprint(news_api)
    ads()
    app.run(host="127.0.0.1", port=5000, debug=True)
