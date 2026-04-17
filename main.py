import datetime
import os

from flask import (
    Flask,
    request,
    render_template,
    redirect,
    abort,
    jsonify,
    session,
    url_for)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)

from data import db_session
from data.news import News
from data.users import User
from data.product import Product
from data.cart import CartItem
from forms.loginform import LoginForm
from forms.news import NewsForm
from forms.user import RegisterForm
from forms.profile import ProfileForm
from forms.product import ProductForm
# для добавления APIs
from apis.users_api import users_api
from apis.news_api import news_api

app = Flask(__name__)
app.config["SECRET_KEY"] = "just_simple_key"
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=365)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):  # если это API — возвращаем JSON
        return jsonify({
            "error": "Not found"
        }), 404
    # иначе обычная страница
    return render_template("404.html"), 404


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

    params = {"user": current_user,
              "title": "Главная - Магазин",
              "promo_products": promo_products}
    return render_template("index.html", **params)


@app.route("/catalog")
def catalog():
    db_sess = db_session.create_session()
    products = db_sess.query(Product).all()

    category = request.args.get('category')  # Фильтрация по категории
    if category:
        products = [p for p in products if p.category == category]

    # Получаем уникальные категории
    categories = list(set([p.category for p in products if p.category]))

    return render_template("catalog.html",
                           title="Каталог товаров",
                           products=products,
                           categories=categories,
                           current_category=category)


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

    return render_template("product_detail.html",
                           title=product.name,
                           product=product,
                           recommended=recommended)


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

    db_sess.commit()

    cart_count = db_sess.query(CartItem).filter(   # Сохраняем количество товаров в корзине в сессию
        CartItem.user_id == current_user.id
    ).count()
    session['cart_count'] = cart_count

    return redirect(url_for('cart'))


@app.route("/cart")
@login_required
def cart():
    db_sess = db_session.create_session()
    cart_items = db_sess.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).all()

    total = sum(item.product.price * item.quantity for item in cart_items)

    return render_template("cart.html",
                           title="Корзина",
                           cart_items=cart_items,
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

    cart_count = db_sess.query(CartItem).filter(
        # Обновляем счетчик корзины
        CartItem.user_id == current_user.id
    ).count()
    session['cart_count'] = cart_count

    return redirect(url_for('cart'))


@app.route("/remove_from_cart/<int:item_id>")
@login_required
def remove_from_cart(item_id):
    db_sess = db_session.create_session()
    cart_item = db_sess.get(CartItem, item_id)

    if cart_item and cart_item.user_id == current_user.id:
        db_sess.delete(cart_item)
        db_sess.commit()

        # Обновляем счетчик корзины
        cart_count = db_sess.query(CartItem).filter(
            CartItem.user_id == current_user.id
        ).count()
        session['cart_count'] = cart_count

    return redirect(url_for('cart'))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()
    db_sess = db_session.create_session()
    user = db_sess.get(User, current_user.id)
    params = {"title": "Личный кабинет", "form": form, "user": user}
    if form.validate_on_submit():
        if db_sess.query(User).filter(User.id != user.id,
                                      User.email == form.email.data).first() is None:
            user.name = form.name.data
            user.email = form.email.data
            user.about = form.about.data
            db_sess.commit()
            return redirect(url_for('profile'))
        params["message"] = "Этот email занят"
    form.name.data = user.name
    form.email.data = user.email
    form.about.data = user.about
    return render_template("profile.html", **params)


@app.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    # Проверка на администратора (можно сделать по email или специальному полю)
    if current_user.email != "admin@example.com":
        abort(403)

    form = ProductForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        product = Product()
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.old_price = form.old_price.data
        product.category = form.category.data
        product.stock = form.stock.data
        product.is_on_sale = form.is_on_sale.data

        db_sess.add(product)
        db_sess.commit()

        return redirect(url_for('catalog'))

    return render_template("add_product.html",
                           title="Добавить товар",
                           form=form)


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
    if request.method == "GET":
        db_sess = db_session.create_session()
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
            name=form.name.data,
            email=form.email.data,
            about=form.about.data)
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
        user = db_sess.query(User).filter(
            User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)

            # Инициализируем корзину при входе
            db_sess = db_session.create_session()
            cart_count = db_sess.query(CartItem).filter(
                CartItem.user_id == user.id
            ).count()
            session['cart_count'] = cart_count

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


# Контекстный процессор для доступа к счетчику корзины во всех шаблонах
@app.context_processor
def inject_cart_count():
    if current_user.is_authenticated:
        return {'cart_count': session.get('cart_count', 0)}
    return {'cart_count': 0}


if __name__ == "__main__":
    # Создаем папку для базы данных если её нет
    if not os.path.exists("db"):
        os.makedirs("db")

    db_session.global_init("db/blogs.sqlite")

    # Добавляем тестовые товары если база пуста
    db_sess = db_session.create_session()
    if db_sess.query(Product).count() == 0:
        test_products = [
            Product(name="Смартфон XYZ", description="Мощный смартфон с отличной камерой и большим экраном",
                    price=29999, old_price=34999, category="Электроника", stock=15, is_on_sale=True),
            Product(name="Ноутбук Pro", description="Идеален для работы и игр, мощный процессор и видеокарта",
                    price=59999, old_price=69999, category="Электроника", stock=8, is_on_sale=True),
            Product(name="Беспроводные наушники", description="Отличное качество звука с шумоподавлением",
                    price=4999, category="Аксессуары", stock=25),
            Product(name="Футболка хлопковая", description="100% хлопок, высокое качество, разные размеры",
                    price=1299, category="Одежда", stock=50, is_on_sale=True),
            Product(name="Джинсы классические", description="Удобные и стильные, подойдут для любого случая",
                    price=3499, category="Одежда", stock=30),
            Product(name="Кроссовки спортивные", description="Для активного отдыха и занятий спортом",
                    price=5999, old_price=7999, category="Обувь", stock=12, is_on_sale=True),
            Product(name="Книга 'Python для начинающих'", description="Лучший учебник по Python с примерами",
                    price=899, category="Книги", stock=45),
            Product(name="Кофеварка автоматическая", description="Ваш идеальный утренний кофе с таймером",
                    price=15999, category="Бытовая техника", stock=5),
        ]

        for product in test_products:
            db_sess.add(product)
        db_sess.commit()

    app.register_blueprint(users_api)
    app.register_blueprint(news_api)
    app.run(host="127.0.0.1", port=5000, debug=True)
