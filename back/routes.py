from flask import render_template, redirect, url_for, request, flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename 
from flask_login import login_required, logout_user, login_user, current_user
from datetime import datetime, timedelta
import os


from app import app, db, UPLOAD_FOLDER
from back.models import User, Product, Category, Cart, Order, OrderProduct


@app.route('/')
def index():
    # Отображает главную страницу с продуктами.
    products = Product.query.all()
    if not products:
        flash('Нет товаров в базе данных')
    return render_template('index.html', products=products)


@app.route('/catalog')
def catalog():
    # Отображает страницу каталога с фильтрацией продуктов по выбранным категориям.
    categories = Category.query.all()
    products = Product.query.all()

    selected_categories = request.args.getlist('category')

    if selected_categories:
        products = Product.query.filter(Product.category_id.in_(selected_categories)).all()

    return render_template('catalog.html', products=products, categories=categories, selected_categories=selected_categories)


@app.route('/profile')
@login_required
def profile():
    # Отображает страницу профиля пользователя в зависимости от его роли.
    user = User.query.filter_by(id=current_user.id).first()
    
    if user.role == 'admin':
        return render_template('admin.html', user=current_user)
    
    elif user.role == 'user':
        orders = Order.query.filter_by(user_id=current_user.id).all()
        return render_template('profile.html', user=current_user, orders=orders)
    
    else:
        return render_template('profile.html', user=current_user)
    

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # Позволяет пользователю редактировать свой профиль.
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.get(current_user.id)
        
        if user:
            user.email = email
            user.password = generate_password_hash(password)
            
            db.session.commit()
            flash('Профиль обновлен')
        else:
            flash('Пользователь не найден')
            
    return render_template('edit_profile.html', user=current_user)


@app.route('/profile/delete/<int:id>', methods=['GET', 'POST'])
def delete_profile(id):
    # Позволяет пользователю удалить свой профиль.
    user = User.query.get(id)
    
    if user is None:
        flash('Пользователь не найден', 'error')
        
        return redirect(url_for('index'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Профиль успешно удален')
        
        return redirect(url_for('index'))
    
    except:
        flash('Ошибка при удалении профиля')
        
        return redirect(url_for('profile'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Обрабатывает процесс входа пользователя в систему.
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email and password:
            user = User.query.filter_by(email=email).first()

            if user and check_password_hash(user.password, password):
                login_user(user)
                
                if user.role == 'admin':
                    return redirect(url_for('admin'))
                else:
                    next_page = request.args.get('next')

                next_page = request.args.get('next')
                
                if next_page:
                    return redirect(next_page)
                else:
                    return redirect(url_for('index'))

            else:
                flash('Почта или пароль введены неверно')
        else:
            flash('Введите почту и пароль')

    return render_template('login.html')


@app.route('/registr',  methods=['GET', 'POST'])
def registr():
    # Обрабатывает процесс регистрации нового пользователя.
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        repeat_password = request.form.get('repeat_password')

        if not (email and password and repeat_password):
            flash('Введите почту и пароль')
        elif password != repeat_password:
            flash('Пароли не совпадают')
        else:
            new_user = User(email=email, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))

    return render_template('registr.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    # Выполняет выход пользователя из системы.
    logout_user()
    
    return redirect(url_for('index'))


@app.after_request
def after_request(response):
    # Перенаправляет неавторизованного пользователя на страницу входа.
    if response.status_code == 401:
        return redirect(url_for('login') + '?next' + request.url)
    
    return response 


@app.route('/order', methods=['GET', 'POST'])
@login_required
def order():
    # Обрабатывает процесс оформления заказа.
    if request.method == 'POST':
        
        user = current_user
        user.surname = request.form.get('surname', user.surname)
        user.name = request.form.get('name', user.name)
        user.phone = request.form.get('phone', user.phone)
        db.session.commit()

        email = request.form.get('email')
        if not email:
            flash('Введите корректный email')
            return redirect(url_for('order'))

        card_number = request.form.get('card_number')
        if not card_number or len(card_number) != 16 or not card_number.isdigit():
            flash('Введите корректный номер карты')
            return redirect(url_for('order'))

        expiration_date = request.form.get('expiration_date')
        if not expiration_date or len(expiration_date) != 4 or not expiration_date.isdigit():
            flash('Введите корректную дату истечения срока действия карты')
            return redirect(url_for('order'))

        cvv = request.form.get('cvv')
        if not cvv or len(cvv) != 3 or not cvv.isdigit():
            flash('Введите корректный CVV')
            return redirect(url_for('order'))

        addres = request.form.get('addres')
        if not addres:
            flash('Введите адрес доставки')
            return redirect(url_for('order'))

        order = Order(
            dateCreation=datetime.now(),
            dateShipping=datetime.now() + timedelta(days=7),
            status='В пути',
            addres=addres,
            user=user
        )
        db.session.add(order)
        db.session.commit()
        
        for product_id, quantity in request.form.items():
            if product_id.startswith('product_id_'):
                product_id = int(product_id.split('_')[-1])
                quantity = int(request.form.get(f'quantity_{product_id}'))
                product = Product.query.get(product_id)
                order_product = OrderProduct(
                    order=order,
                    product=product,
                    quantity=quantity
                )
                db.session.add(order_product)
        db.session.commit()

        flash('Заказ успешно оформлен!')
        return redirect(url_for('profile'))

    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    products = []
    total_quantities = {}
    total_prices = {}
    total_price = 0
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)
        products.append((product, cart_item.quantity))
        total_quantities[product.id] = cart_item.quantity
        total_prices[product.id] = product.price * cart_item.quantity
        total_price += product.price * cart_item.quantity

    return render_template('order.html', products=products, total_quantities=total_quantities, total_prices=total_prices, total_price=total_price)


@app.route('/order/products/<int:id>', methods=['GET'])
@login_required
def order_products(id):
    order = Order.query.get_or_404(id)
    return render_template('order_products.html', order=order)


@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    if request.method == 'POST':
        product_id = int(request.form.get('product_id'))
        product = Product.query.get(product_id)
        
        if product:
            cart = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
            
            if cart:
                if request.form.get('operation') == '-':
                    if cart.quantity > 1:
                        cart.quantity -= 1
                        db.session.commit()
                    else:
                        db.session.delete(cart)
                        db.session.commit()
                        
                elif request.form.get('operation') == '+':
                    cart.quantity += 1
                    db.session.commit()
                
            else:
                cart = Cart(user_id=current_user.id, product_id=product_id, quantity=1)
                db.session.add(cart)
                db.session.commit()
            
        return redirect(url_for('cart'))
    
    user_id = current_user.id
    carts = Cart.query.filter_by(user_id=user_id).all()
    products = []
    total_quantities = {}
    total_prices = {}
    
    for cart in carts:
        product = Product.query.get(cart.product_id)
        
        if product.id in total_quantities:
            total_quantities[product.id] += cart.quantity
            total_prices[product.id] += product.price * cart.quantity
        else:
            total_quantities[product.id] = cart.quantity
            total_prices[product.id] = product.price * cart.quantity
        
        products.append(product)
    
    
    if not products:
        flash('Ваша корзина пуста')
    
    return render_template('cart.html', products=products, total_quantities=total_quantities, total_prices=total_prices)


@app.route('/cart/delete/<int:product_id>', methods=['GET', 'POST'])
@login_required
def cart_delete(product_id):
    cart = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart:
        db.session.delete(cart)
        db.session.commit()
        
    return redirect(url_for('cart'))


@app.route('/product/<name>/<int:id>')
def product(id, name):
    product = Product.query.get(id)
    if product is None:
        return redirect(url_for('index'))
    recommended_products = Product.query.all()[:3]
    return render_template('product.html', product=product, recommended_products=recommended_products)


@app.route('/admin')
@login_required
def admin():
    categories = Category.query.all()
    products = Product.query.all()
    return render_template('admin.html', categories=categories, products=products, user=current_user)


@app.route('/admin/product')
@login_required
def admin_product():
    product = Product.query.all()
    return render_template('admin_product.html', product=product, user=current_user)


@app.route('/admin/product/add', methods=['GET', 'POST'])
def add_product():
    categories = Category.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        img = request.files['img']
        category_id = request.form.get('category_id')
        
        if name and price and category_id and img:
            try:
                price = int(price)
            except ValueError:
                flash('Недопустимое значение цены')
                return redirect(url_for('add_product'))
            
            if price <= 0:
                flash('Цена должна быть положительным числом')
                return redirect(url_for('add_product'))
            
            filename = secure_filename(img.filename)
            img.save(os.path.join(UPLOAD_FOLDER, filename))
            
            category = Category.query.get(category_id)
            if category:
                product = Product(name=name, price=price, img=filename, category=category)
                db.session.add(product)
                db.session.commit()
                
                flash('Продукт успешно добавлен')
                return redirect(url_for('admin_product'))
            
            else:
                flash('Выбранная категория не существует')
                return redirect(url_for('add_product'))
            
        else:
            flash('Заполните все поля и выберите файл для загрузки')
            return redirect(url_for('add_product'))
            
    return render_template('add_admin_product.html', user=current_user, categories=categories)


@app.route('/admin/product/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    categories = Category.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        img = request.files.get('img')
        category_id = request.form.get('category_id')
        
        if name and price:
            product = Product.query.get(id)
            category = Category.query.get(category_id)
            
            if category:
                product.category = category
                
            if img:
                product.img = img
            else:
                product.img = product.img
            
            product.name = name
            product.price = price
            
            db.session.commit()
            return redirect(url_for('admin_product'))
        
        else:
            flash('Заполните все поля')
            return redirect(url_for('edit_product', id=id))  
    
    product = Product.query.get(id)
    return render_template('edit_admin_product.html', product=product, user=current_user, categories=categories)


@app.route('/admin/product/delete/<int:id>', methods=['POST'])
def delete_product(id):
    # Сначала удаляем все связанные записи в таблице cart
    cart_items = Cart.query.filter_by(product_id=id).all()
    for item in cart_items:
        db.session.delete(item)
    db.session.commit()

    # Теперь удаляем сам продукт
    product = Product.query.get_or_404(id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Продукт успешно удален')
        return redirect(url_for('admin_product'))
    except:
        flash('При удалении товара произошла ошибка')
        return redirect(url_for('admin_product'))



@app.route('/admin/category')
def admin_category():
    category = Category.query.all()
    return render_template('admin_category.html', category=category, user=current_user)


@app.route('/admin/category/add', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        name = request.form.get('name')
        
        if name:
            existing_category = Category.query.filter_by(name=name).first()
            
            if existing_category:
                flash('Категория с таким именем уже существует')
                return redirect(url_for('add_category'))
            
            category = Category(name=name)   
            db.session.add(category)
            db.session.commit()
            
            flash('Категория успешно добавлена')
            return redirect(url_for('admin_category'))
        
        else:
            flash('Введите название категории')   
    return render_template('add_admin_category.html', user=current_user)


@app.route('/admin/category/edit/<int:id>', methods=['GET','POST'])
def edit_category(id):
    category = Category.query.get(id)
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            category.name = name
            db.session.commit()
            flash('Категория успешно обновлена', 'success')
            return redirect(url_for('admin_category'))
        else:
            flash('Введите название категории')
    return render_template('edit_admin_category.html', category=category, user=current_user)


@app.route('/admin/category/delete/<int:id>', methods=['GET','POST'])
def delete_category(id):
    category = Category.query.get(id)
    
    if category:
        db.session.delete(category)
        db.session.commit()
        flash('Категория успешно удалена', 'success')
    else:
        flash('Категория не найдена', 'error')
    return redirect(url_for('admin_category'))