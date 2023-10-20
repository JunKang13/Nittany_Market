# package imported
from datetime import date
from flask import Flask, render_template, request, session, redirect, url_for
import pymysql
import hashlib
from urllib.parse import unquote

# define connection to MySQL
conn = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='020321',
    port=3306,
    db='phase2'
)

# define app
app = Flask(__name__)
# define secret key and session
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'


# select all users from the database
def query_data():
    sql = """select * from users"""
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(sql)
    return cursor.fetchall()


# query out the database according to the input sql
def query_buyer_info(sql):
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(sql)
    return cursor.fetchall()


# some global variables
# get all category sql
sql = """select distinct parent from categories"""
# all category
data = query_buyer_info(sql)
# get all sub categories(idk)
sub = {}
for i in range(len(data)):
    one = '{1}{0}{1}'.format(data[i]['parent'], "'")
    sql1 = """select distinct category_name from categories where parent = """ + one
    sub[data[i]['parent']] = query_buyer_info(sql1)


# set the buyer only page route
@app.route('/index1/<string:email>/<string:fname>/<string:lname>/')
def index1(email, fname, lname):
    # category dictionary
    sub = {}
    # loop through all categories
    for i in range(len(data)):
        # get the parent name and query all subs under the parent category
        temp = '{1}{0}{1}'.format(data[i]['parent'], "'")
        sql_cat = """select distinct category_name from categories where parent = """ + temp
        # for all subs under the specific parent, attach the list to the value of dict
        sub[data[i]['parent']] = query_buyer_info(sql_cat)
    # render the index page for buyer only
    return render_template('index1.html', data=data, sub=sub)


# set the both seller & buyer page route
@app.route('/index2/<string:email>/<string:fname>/<string:lname>/')
def index2(email, fname, lname):
    # category dictionary
    sub = {}
    # get the login email, and query for the user's name
    email = '{1}{0}{1}'.format(session['user_info'], "'")
    user_sql = """select * from buyers where buyers.email = """ + email
    name = query_buyer_info(user_sql)[0]['first_name']
    # loop through all categories
    for i in range(len(data)):
        # get the parent name and query all subs under the parent category
        temp = '{1}{0}{1}'.format(data[i]['parent'], "'")
        sql_cat = """select distinct category_name from categories where parent = """ + temp
        # for all subs under the specific parent, attach the list to the value of dict
        sub[data[i]['parent']] = query_buyer_info(sql_cat)
    # render the index page for both buyer and seller
    return render_template('index2.html', data=data, sub=sub, name=name)


# set the seller or vendors only page route
@app.route('/index3/<string:email>/')
def index3(email):
    # category dictionary
    sub = {}
    # loop through all categories
    for i in range(len(data)):
        # get the parent name and query all subs under the parent category
        temp = '{1}{0}{1}'.format(data[i]['parent'], "'")
        sql_cat = """select distinct category_name from categories where parent = """ + temp
        # for all subs under the specific parent, attach the list to the value of dict
        sub[data[i]['parent']] = query_buyer_info(sql_cat)
    # render the index page for seller or vendors only
    return render_template('index3.html', data=data, sub=sub)


# set the login page route
@app.route('/login/')
def login_page():
    # render the login page
    return render_template('login.html')


# set the info page for buyer only route
@app.route('/info/')
def info_page():
    # get the login email, and query for the user's name, age, gender
    email = '{1}{0}{1}'.format(session['user_info'], "'")
    user_sql = """select * from buyers where buyers.email = """ + email
    email_with_enter = '{1}{0}{2}{1}'.format(session['user_info'], "'", "\r")
    name = query_buyer_info(user_sql)[0]['first_name'] + ' ' + query_buyer_info(user_sql)[0]['last_name']
    age = query_buyer_info(user_sql)[0]['age']
    gender = query_buyer_info(user_sql)[0]['gender']

    # query out the credit card result from given email
    credit_sql = """select * from credit where credit.owner_email = """ + email_with_enter
    credit = query_buyer_info(credit_sql)[0]['credit_card_num'].split("-")[-1]
    credit_type = query_buyer_info(credit_sql)[0]['card_type']

    # query out the billing & delivering address, including street num, street, city, state, zipcode
    sql4 = """select * from address where address_id = """
    sql5 = """select * from zipcode_info where zipcode = """
    homeid = '{1}{0}{1}'.format(query_buyer_info(user_sql)[0]['home_address_id'], "'")
    billid = '{1}{0}{1}'.format(query_buyer_info(user_sql)[0]['billing_address_id'].split("\r")[0], "'")
    homestreet_sql = query_buyer_info(sql4 + homeid)[0]
    home_zip = '{1}{0}{1}'.format(homestreet_sql['zipcode'], "'")
    billstreet_sql = query_buyer_info(sql4 + billid)[0]
    bill_zip = '{1}{0}{1}'.format(billstreet_sql['zipcode'], "'")
    home_zip_sql = query_buyer_info(sql5 + home_zip)[0]
    bill_zip_sql = query_buyer_info(sql5 + bill_zip)[0]
    homeadd = unquote(
        str(homestreet_sql['street_num']) + ' ' + homestreet_sql['street_name'] + ', ' + home_zip_sql[
            'city'] + ', ' + home_zip_sql['state_id'] + ', ' + home_zip_sql['zipcode'])
    billadd = str(billstreet_sql['street_num']) + ' ' + billstreet_sql['street_name'] + ', ' + \
              bill_zip_sql['city'] + ', ' + bill_zip_sql['state_id'] + ', ' + bill_zip_sql['zipcode']

    # query out the order of the user
    order_sql = """select * from orders where buyer_email = """ + email
    order = query_buyer_info(order_sql)

    # query out the shopping cart of the user
    cart_sql = """select * from cart where buyer_email = """ + email
    cart = query_buyer_info(cart_sql)
    ind = 0
    # loop through the result and filter out products being valid only, for invalid ones, cut them off
    for i in cart:
        clid = str(i['listing_id'])
        valid_sql = """select * from products where v_product = 1 and listing_id = """ + clid
        valid = query_buyer_info(valid_sql)
        if len(valid) == 0:
            del cart[ind]
        ind += 1

    # if the user does not have any order here, then customize the order to be no record
    if len(order) == 0:
        order = [{'transaction_id': 'No record', 'quantity': '', 'payment': ''}]

    # render the info page with necessary info
    return render_template('info.html', email=session['user_info'], name=name, age=age, gender=gender, credit=credit,
                           credit_type=credit_type, home=homeadd, bill=billadd, order=order, cart=cart)


# set the info page for both buyer & seller route
@app.route('/info1/')
def info_page1():
    # get the login email, and query for the user's name, age, gender
    email = '{1}{0}{1}'.format(session['user_info'], "'")
    user_sql = """select * from buyers where buyers.email = """ + email
    email_with_enter = '{1}{0}{2}{1}'.format(session['user_info'], "'", "\r")
    name = query_buyer_info(user_sql)[0]['first_name'] + ' ' + query_buyer_info(user_sql)[0]['last_name']
    age = query_buyer_info(user_sql)[0]['age']
    gender = query_buyer_info(user_sql)[0]['gender']

    # query out the credit card result from given email
    credit_sql = """select * from credit where credit.owner_email = """ + email_with_enter
    credit = query_buyer_info(credit_sql)[0]['credit_card_num'].split("-")[-1]
    credit_type = query_buyer_info(credit_sql)[0]['card_type']

    # query out the billing & delivering address, including street num, street, city, state, zipcode
    sql4 = """select * from address where address_id = """
    sql5 = """select * from zipcode_info where zipcode = """
    homeid = '{1}{0}{1}'.format(query_buyer_info(user_sql)[0]['home_address_id'], "'")
    billid = '{1}{0}{1}'.format(query_buyer_info(user_sql)[0]['billing_address_id'].split("\r")[0], "'")
    homestreet_sql = query_buyer_info(sql4 + homeid)[0]
    home_zip = '{1}{0}{1}'.format(homestreet_sql['zipcode'], "'")
    billstreet_sql = query_buyer_info(sql4 + billid)[0]
    bill_zip = '{1}{0}{1}'.format(billstreet_sql['zipcode'], "'")
    home_zip_sql = query_buyer_info(sql5 + home_zip)[0]
    bill_zip_sql = query_buyer_info(sql5 + bill_zip)[0]
    homeadd = unquote(
        str(homestreet_sql['street_num']) + ' ' + homestreet_sql['street_name'] + ', ' + home_zip_sql[
            'city'] + ', ' + home_zip_sql['state_id'] + ', ' + home_zip_sql['zipcode'])
    billadd = str(billstreet_sql['street_num']) + ' ' + billstreet_sql['street_name'] + ', ' + \
              bill_zip_sql['city'] + ', ' + bill_zip_sql['state_id'] + ', ' + bill_zip_sql['zipcode']

    # query out the average rating and overall balance of the user as a seller
    rating_sql = """select avg(rating) from ratings where ratings.seller_email = """ + email
    balance_sql = """select balance from sellers where sellers.email = """ + email
    rating = query_buyer_info(rating_sql)[0]['avg(rating)']
    balance = query_buyer_info(balance_sql)[0]['balance']

    # query out all products listed by the user as a seller
    product_sql = """select * from products where seller_email = """ + email
    product = query_buyer_info(product_sql)

    # if there is no product, customize as null
    if len(product) == 0:
        product = [{'title': 'Null', 'product_name': ''}]

    # query out the order of the user
    order_sql = """select * from orders where buyer_email = """ + email
    order = query_buyer_info(order_sql)

    # if the user does not have any order here, then customize the order to be no record
    if len(order) == 0:
        order = [{'transaction_id': 'No record', 'quantity': '', 'payment': ''}]

    # query out the shopping cart of the user
    cart_sql = """select * from cart where buyer_email = """ + email
    cart = query_buyer_info(cart_sql)
    ind = 0
    for i in cart:
        clid = str(i['listing_id'])
        valid_sql = """select * from products where v_product = 1 and listing_id = """ + clid
        valid = query_buyer_info(valid_sql)
        if len(valid) == 0:
            del cart[ind]
        ind += 1

    # render the info page with necessary info
    return render_template('info1.html', email=session['user_info'], name=name, age=age, gender=gender, credit=credit,
                           credit_type=credit_type, home=homeadd, bill=billadd, balance=balance, rating=rating,
                           product=product, order=order, cart=cart)


# set the info page for seller or vendors only route
@app.route('/sellerinfo/')
def seller_info_page():
    # get the email and query out the average rating and overall balance of the user as a seller
    email = '{1}{0}{1}'.format(session['user_info'], "'")
    rating_sql = """select avg(rating) from ratings where ratings.seller_email = """ + email
    balance_sql = """select balance from sellers where sellers.email = """ + email
    rating = query_buyer_info(rating_sql)[0]['avg(rating)']
    balance = query_buyer_info(balance_sql)[0]['balance']

    # query out all products listed by the user as a seller
    product_sql = """select * from products where seller_email = """ + email
    product = query_buyer_info(product_sql)

    # if there is no product, customize as null
    if len(product) == 0:
        product = [{'title': 'Null', 'product_name': ''}]

    # render the info page with necessary info
    return render_template('sellerinfo.html', email=session['user_info'], balance=balance, rating=rating,
                           product=product)


# set the info page for product listing route
@app.route('/list/')
def list():
    # render the listing page with necessary info
    return render_template('list.html', data=data, sub=sub, name=session['user_info'])


# set the empty list page for product listing route
@app.route('/emptylist/')
def emptylist():
    # render the empty listing page with necessary info
    return render_template('emptylist.html', data=data, sub=sub, name=session['user_info'])


# set the index page route
@app.route('/')
def index():
    # render the index page with necessary info
    return render_template('index.html', data=data, sub=sub)


# config the route&method for login page
@app.route('/login/', methods=['GET', "POST"])
def login():
    # when requesting info, return the login page
    if request.method == 'GET':
        return render_template('login.html')
    if request.path == '/login/':
        # o/w, get the data collected from the login form, cast pwd and encode it to utf-8 then use md5 to encode
        user = request.form.get('email')
        pwd = request.form.get('password') + '\r'
        md5_obj = hashlib.md5(pwd.encode('utf-8')).hexdigest()
        # for all users' info, if there's any matched, store the session and redirect to the home page (return success)
        for check in query_data():
            if user == check['email']:
                print(check['password'])
            if user == check['email'] and md5_obj == check['password']:
                session['user_info'] = user
                var = '{1}{0}{1}'.format(user, "'")
                # declare sql to get seller info if applicable, get vendors info if applicable, get buyers info iff
                # applicable
                sql2 = """select * from sellers where sellers.email = """ + var
                sql3 = """select * from local_vendors where local_vendors.email = """ + var
                sql = """select * from buyers where buyers.email = """ + var

                # buyer only, return buyer only page
                if len(query_buyer_info(sql2)) == 0 and len(query_buyer_info(sql3)) == 0:
                    return redirect(url_for('index1', email=user, fname=query_buyer_info(sql)[0]['first_name'],
                                            lname=query_buyer_info(sql)[0]['last_name'],
                                            sub=sub))

                # both buyer and seller, return buyer&seller page
                elif len(query_buyer_info(sql2)) != 0 and len(query_buyer_info(sql)) != 0:
                    return redirect(url_for('index2', email=user, fname=query_buyer_info(sql)[0]['first_name'],
                                            lname=query_buyer_info(sql)[0]['last_name'], sub=sub))

                # only seller or vendors, return seller page
                elif ((len(query_buyer_info(sql2)) != 0 or len(query_buyer_info(sql3)) != 0) and (
                        len(query_buyer_info(sql)) == 0)):
                    return redirect(url_for('index3', email=user, sub=sub))
        # o/w, return error msg
        return render_template('login.html', msg='The email or password you entered may be incorrect!')


# config the route&method for seller&buyer info page
@app.route('/info1/', methods=['GET', "POST"])
def info1():
    if request.method == 'POST':
        # get the user email, password
        email = request.form.get('email')
        pwd = request.form.get('pwd') + '\r'
        pwd = '{1}{0}{1}'.format(pwd, "'")
        email = '{1}{0}{1}'.format(email, "'")
        # define the changepwd sql, update the password field
        changepwd_sql = """update users set password =MD5( """ + pwd + """) where email = """ + email
        # save changes
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(changepwd_sql)
        conn.commit()
    # return the login page
    return render_template('login.html')


# config the route&method for buyer only info page
@app.route('/info/', methods=['GET', "POST"])
def info():
    if request.method == 'POST':
        # get the user email, password
        email = request.form.get('email')
        pwd = request.form.get('pwd') + '\r'
        pwd = '{1}{0}{1}'.format(pwd, "'")
        email = '{1}{0}{1}'.format(email, "'")
        # define the changepwd sql, update the password field
        changepwd_sql = """update users set password =MD5( """ + pwd + """) where email = """ + email
        # save changes
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(changepwd_sql)
        conn.commit()
    # return the login page
    return render_template('login.html')

# config the route&method for seller/vendors only info page
@app.route('/sellerinfo/', methods=['GET', "POST"])
def sellerinfo():
    if request.method == 'POST':
        # get the user email, password
        email = request.form.get('email')
        pwd = request.form.get('pwd') + '\r'
        pwd = '{1}{0}{1}'.format(pwd, "'")
        email = '{1}{0}{1}'.format(email, "'")
        # define the changepwd sql, update the password field
        changepwd_sql = """update users set password =MD5( """ + pwd + """) where email = """ + email
        # save changes
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(changepwd_sql)
        conn.commit()
    # return the login page
    return render_template('login.html')


# config the route&method for listing page
@app.route('/list/', methods=['GET', "POST"])
def index11():
    if request.method == 'POST':
        # get the name
        s = format(request.form.get('s'))
        # if it's a name instead of seller, get the email from session and retrieve the name
        if s != 'Seller':
            email = '{1}{0}{1}'.format(session['user_info'], "'")
            user_sql = """select first_name from buyers where buyers.email = """ + email
            name = query_buyer_info(user_sql)[0]['first_name']
        # o/w, keep seller
        else:
            name = 'Seller'

        # get category selected and query out products under that category
        cat = '{1}{0}{1}'.format(request.form.get('cat'), "'")
        cat_sql = """select title, product_name, price, listing_id from products where category = """ + cat + """and v_product = 1"""
        item = query_buyer_info(cat_sql)
        # if no products, then customize to be null and rreturn empty list
        if len(item) == 0:
            return render_template('emptylist.html', cat=request.form.get('cat'), data=data, sub=sub, name=name)

        # else, return the listing page and show all products
        else:
            return render_template('list.html', cat=request.form.get('cat'), data=data, sub=sub, item=item, name=name,
                                   len=len(item))


# config the route&method for product detail info page
@app.route('/detail/', methods=['GET', "POST"])
def detail1():
    if request.method == 'POST':
        # get the listing_id and query out the product info, also get the review of the product
        lid = str(request.form.get('lid'))
        lid_sql = """select * from products where listing_id = """ + lid
        item = query_buyer_info(lid_sql)[0]
        review_sql = """select * from reviews where listing_id = """ + lid
        review = query_buyer_info(review_sql)

        # if there's no review, customize review to be no review
        if len(review) == 0:
            review = [
                {'buyer_email': 'No Reviews For this product', 'seller_email': '', 'listing_id': '', 'review_desc': ''}]

        # get the name
        s = format(request.form.get('s'))
        # if it's a name instead of seller, get the email from session and retrieve the user info, credit card info,
        # and address info
        if s != 'Seller':
            email = '{1}{0}{1}'.format(session['user_info'], "'")
            user_sql = """select * from buyers where buyers.email = """ + email
            uinfo = query_buyer_info(user_sql)[0]
            email_c = '{1}{0}{2}{1}'.format(session['user_info'], "'", "\r")
            credit_sql = """select * from credit where owner_email = """ + email_c
            credit = query_buyer_info(credit_sql)
            homeaddnum = '{1}{0}{1}'.format(uinfo['home_address_id'], "'")
            home_sql = """select * from address where address_id = """ + homeaddnum
            home = query_buyer_info(home_sql)[0]
            # return the product detail info page with necessary info
            return render_template('detail.html', lid=lid, name=s, item=item, info=uinfo, credit=credit, home=home,
                                   review=review)
        # o/w, customize credit card and userinfo to be null
        else:
            return render_template('deny.html', cat=request.form.get('cat'), data=data, sub=sub, name='Seller')







# config the route&method for info page to unlist products
@app.route('/info1/1', methods=['GET', "POST"])
def xiajia():
    if request.method == 'POST':
        # get today date
        d = '{1}{0}{1}'.format(date.today(), "'")
        # get listing id and set that product to be not valid
        lid = request.form.get('lid')
        changed_sql = """update products set v_product = 0, period = """ + d + """ where listing_id = """ + lid
        # save changes
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(changed_sql)
        conn.commit()

        # get the user email, get the credit card, name age, gender info
        email = '{1}{0}{1}'.format(session['user_info'], "'")
        user_sql = """select * from buyers where buyers.email = """ + email
        email_with_enter = '{1}{0}{2}{1}'.format(session['user_info'], "'", "\r")
        credit_sql = """select * from credit where credit.owner_email = """ + email_with_enter
        name = query_buyer_info(user_sql)[0]['first_name'] + ' ' + query_buyer_info(user_sql)[0]['last_name']
        age = query_buyer_info(user_sql)[0]['age']
        gender = query_buyer_info(user_sql)[0]['gender']
        credit = query_buyer_info(credit_sql)[0]['credit_card_num'].split("-")[-1]
        credit_type = query_buyer_info(credit_sql)[0]['card_type']

        # get home/billing address info
        sql4 = """select * from address where address_id = """
        sql5 = """select * from zipcode_info where zipcode = """
        homeid = '{1}{0}{1}'.format(query_buyer_info(user_sql)[0]['home_address_id'], "'")
        billid = '{1}{0}{1}'.format(query_buyer_info(user_sql)[0]['billing_address_id'].split("\r")[0], "'")
        homestreet_sql = query_buyer_info(sql4 + homeid)[0]
        home_zip = '{1}{0}{1}'.format(homestreet_sql['zipcode'], "'")
        billstreet_sql = query_buyer_info(sql4 + billid)[0]
        bill_zip = '{1}{0}{1}'.format(billstreet_sql['zipcode'], "'")
        home_zip_sql = query_buyer_info(sql5 + home_zip)[0]
        bill_zip_sql = query_buyer_info(sql5 + bill_zip)[0]
        homeadd = unquote(
            str(homestreet_sql['street_num']) + ' ' + homestreet_sql['street_name'] + ', ' + home_zip_sql[
                'city'] + ', ' + home_zip_sql['state_id'] + ', ' + home_zip_sql['zipcode'])
        billadd = str(billstreet_sql['street_num']) + ' ' + billstreet_sql['street_name'] + ', ' + \
                  bill_zip_sql['city'] + ', ' + bill_zip_sql['state_id'] + ', ' + bill_zip_sql['zipcode']

        # get the avg rating and overall balance of the seller if applicable
        rating_sql = """select avg(rating) from ratings where ratings.seller_email = """ + email
        balance_sql = """select balance from sellers where sellers.email = """ + email
        rating = query_buyer_info(rating_sql)[0]['avg(rating)']
        balance = query_buyer_info(balance_sql)[0]['balance']

        # get the product listed by the user as a seller
        product_sql = """select * from products where seller_email = """ + email
        product = query_buyer_info(product_sql)
        # if there ain't no products, customize as null
        if len(product) == 0:
            product = [{'title': 'Null', 'product_name': ''}]

        # get the order of the user as a buyer
        order_sql = """select * from orders where buyer_email = """ + email
        order = query_buyer_info(order_sql)

        # if there's no order, customize as no record
        if len(order) == 0:
            order = [{'transaction_id': 'No record', 'quantity': '', 'payment': ''}]

        # render the info page with necessary info
        return render_template('info1.html', email=session['user_info'], name=name, age=age, gender=gender,
                               credit=credit,
                               credit_type=credit_type, home=homeadd, bill=billadd, balance=balance, rating=rating,
                               product=product, order=order)


# config the route&method for info page to unlist products
@app.route('/sellerinfo/1', methods=['GET', "POST"])
def xiajia2():
    if request.method == 'POST':
        # get today date
        d = '{1}{0}{1}'.format(date.today(), "'")
        # get listing id and set that product to be not valid
        lid = request.form.get('lid')
        changed_sql = """update products set v_product = 0, period = """ + d + """ where listing_id = """ + lid
        # save changes
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(changed_sql)
        conn.commit()

        # get the user email, get the avg rating and overall balance
        email = '{1}{0}{1}'.format(session['user_info'], "'")
        rating_sql = """select avg(rating) from ratings where ratings.seller_email = """ + email
        balance_sql = """select balance from sellers where sellers.email = """ + email
        rating = query_buyer_info(rating_sql)[0]['avg(rating)']
        balance = query_buyer_info(balance_sql)[0]['balance']

        # get the product listed by the user as a seller
        product_sql = """select * from products where seller_email = """ + email
        product = query_buyer_info(product_sql)
        # if there ain't no products, customize as null
        if len(product) == 0:
            product = [{'title': 'Null', 'product_name': ''}]

        # render the seller info page with necessary info
        return render_template('sellerinfo.html', email=session['user_info'], balance=balance, rating=rating,
                               product=product)


# config the route&method for info page to list new products
@app.route('/index3/s', methods=['GET', "POST"])
def xinjian():  # 已经有了2598 和2599 两个新商品
    if request.method == 'POST':
        # get the parent category, sub category
        parent = '{1}{0}{1}'.format(request.form.get('parent123'), "'")
        sub1 = '{1}{0}{2}{1}'.format(request.form.get('sub123'), "'", "\r")
        sub2 = '{1}{0}{1}'.format(request.form.get('sub123'), "'")
        # try to add new category
        newcat_sql = """insert into categories (parent, category_name) values (""" + parent + """,""" + sub1 + """)"""
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(newcat_sql)
            conn.commit()
        except:
            print('wrong')

        # get the max lid, and could derive a new lid for the new product
        lid_sql = """select max(listing_id) from products"""
        lid = str(query_buyer_info(lid_sql)[0]['max(listing_id)'] + 1)
        # get the seller email, product title, name, price, quantity, description
        selleremail = '{1}{0}{1}'.format(request.form.get('email123'), "'")
        title = '{1}{0}{1}'.format(request.form.get('title123'), "'")
        p_name = '{1}{0}{1}'.format(request.form.get('name123'), "'")
        price = str(request.form.get('price123'))
        quantity = str(request.form.get('quantity123'))
        des = '{1}{0}{1}'.format(request.form.get('des123'), "'")

        # try to insert to the product table
        newprod_sql = """insert into products (seller_email, listing_id, category, title, product_name,product_description, price, quantity) values (""" + selleremail + """,""" + lid + """,""" + sub2 + """,""" + title + """,""" + p_name + """,""" + des + """,""" + price + """,""" + quantity + """)"""
        try:
            cursor.execute(newprod_sql)
            conn.commit()
        except:
            print("wrong123")

        # render the index page
        return render_template('index3.html', data=data, sub=sub)


# config the route&method for info page to list new products
@app.route('/index2/s', methods=['GET', "POST"])
def xinjian2():  # 已经有了2598 和2599 两个新商品 还有2600
    if request.method == 'POST':
        # get the parent category, sub category
        parent = '{1}{0}{1}'.format(request.form.get('parent123'), "'")
        sub1 = '{1}{0}{2}{1}'.format(request.form.get('sub123'), "'", "\r")
        sub2 = '{1}{0}{1}'.format(request.form.get('sub123'), "'")
        # try to add new category
        newcat_sql = """insert into categories (parent, category_name) values (""" + parent + """,""" + sub1 + """)"""
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(newcat_sql)
            conn.commit()
        except:
            print('wrong')

        # get the max lid, and could derive a new lid for the new product
        lid_sql = """select max(listing_id) from products"""
        lid = str(query_buyer_info(lid_sql)[0]['max(listing_id)'] + 1)

        # get the seller email, product title, name, price, quantity, description
        selleremail = '{1}{0}{1}'.format(request.form.get('email123'), "'")
        title = '{1}{0}{1}'.format(request.form.get('title123'), "'")
        p_name = '{1}{0}{1}'.format(request.form.get('name123'), "'")
        price = str(request.form.get('price123'))
        quantity = str(request.form.get('quantity123'))
        des = '{1}{0}{1}'.format(request.form.get('des123'), "'")

        # try to insert to the product table
        newprod_sql = """insert into products (seller_email, listing_id, category, title, product_name,product_description, price, quantity) values (""" + selleremail + """,""" + lid + """,""" + sub2 + """,""" + title + """,""" + p_name + """,""" + des + """,""" + price + """,""" + quantity + """)"""
        try:
            cursor.execute(newprod_sql)
            conn.commit()
        except:
            print("wrong123")

        # get the first name from the email
        selleremail = '{1}{0}{1}'.format(request.form.get('email123'), "'")
        user_sql = """select * from buyers where buyers.email = """ + selleremail
        name = query_buyer_info(user_sql)[0]['first_name']

        # render the index page
        return render_template('index2.html', name=name, data=data, sub=sub)


# config the route&method to buy products
@app.route('/detail/b', methods=['GET', "POST"])
def goumai():  # 已经有了2598 和2599 两个新商品 还有2600
    if request.method == 'POST':
        # get the seller email, listing id, buyer email, today's date, quantity, payment, total quantity
        selleremail = '{1}{0}{1}'.format(request.form.get('selleremail'), "'")
        lid = str(request.form.get('lid'))
        buyeremail = '{1}{0}{1}'.format(request.form.get('buyeremail'), "'")
        buyeremail_forcredit = '{1}{0}{2}{1}'.format(request.form.get('buyeremail'), "'", "\r")
        d = '{1}{0}{1}'.format(date.today(), "'")
        quantity = str(request.form.get('quantity'))
        quantity_int = int(request.form.get('quantity'))
        total_quantity = int(request.form.get('totalquantity'))
        payment = str(request.form.get('pay'))

        # get the max transaction_id and give the new tid
        gettid_sql = """select max(transaction_id) from orders"""
        tid = str(query_buyer_info(gettid_sql)[0]['max(transaction_id)'] + 1)

        # insert the new order into the order table
        buy_sql = """insert into orders (transaction_id, seller_email, listing_id, buyer_email, date, quantity, payment) values (""" + tid + """,""" + selleremail + """,""" + lid + """,""" + buyeremail + """,""" + d + """,""" + quantity + """,""" + payment + """)"""
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(buy_sql)
            conn.commit()
            print('success')
        except:
            print('wrong!!!!!')

        # update remain quantity
        remain = str(total_quantity - quantity_int)
        updatequantity_sql = """update products set quantity = """ + remain + """ where listing_id = """ + lid
        try:
            cursor.execute(updatequantity_sql)
            conn.commit()
            print('success')
        except:
            print('wrong!!!!!')

        # if no remained, update the product as invalid
        if remain == 0:
            updatevalid_sql = """update products set v_product = 0, period = """ + d + """ where listing_id = """ + lid
            try:
                cursor.execute(updatevalid_sql)
                conn.commit()
                print('success')
            except:
                print('wrong!!!!!123')

        # if choose to add new credit card, get the card number , expiration, cvv
        if (len(request.form.get('newcredit')) == 16):
            newcredit = '{1}{0}{1}'.format(request.form.get('newcredit'), "'")
            newdd = request.form.get('newdd').split('/')
            newcvv = '{1}{0}{1}'.format(request.form.get('newcvv'), "'")
            # insert in to the credit table
            newcc_sql = """insert into credit (credit_card_num, card_code, expire_month, expire_year, owner_email) values (""" + newcredit + """,""" + newcvv + """,""" + \
                        newdd[0] + """,""" + newdd[1] + """,""" + buyeremail_forcredit + """)"""
            try:
                cursor.execute(newcc_sql)
                conn.commit()
                print('success')
            except:
                print('wrong!!!!!123')
        # return the detail page
        return detail1()


# config the route&method to review orders/sellers
@app.route('/info/r', methods=['GET', "POST"])
def review():
    if request.method == 'POST':
        # get the seller email, listing id, buyer email, description
        selleremailr = '{1}{0}{1}'.format(request.form.get('selleremailr'), "'")
        buyeremailr = '{1}{0}{1}'.format(request.form.get('buyeremailr'), "'")
        lidr = str(request.form.get('lidr'))
        descr = '{1}{0}{1}'.format(request.form.get('descr'), "'")

        # insert into the review table
        review_sql = """insert into reviews (buyer_email, seller_email, listing_id, review_desc) values (""" + buyeremailr + """,""" + selleremailr + """,""" + lidr + """,""" + descr + """)"""
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(review_sql)
            conn.commit()
            print('success')
        except:
            print('wrong!!!!!')

        # get today's date, the seller rate
        d = '{1}{0}{1}'.format(date.today(), "'")
        rates = str(request.form.get('ratpo'))
        r = request.form.get('ratpo')

        # based on the rate value, give different rate description
        if int(r) == 1:
            rd = 'Bad'
        elif int(r) == 2 or int(rates) == 3:
            rd = 'Not Bad'
        else:
            rd = 'Awesome'
        rd = '{1}{0}{1}'.format(rd, "'")
        # insert into ratings table
        rate_sql = """insert into ratings (buyer_email, seller_email, date, rating, review_desc) values (""" + buyeremailr + """,""" + selleremailr + """,""" + d + """,""" + rates + """,""" + rd + """)"""
        try:
            cursor.execute(rate_sql)
            conn.commit()
            print('success')
        except:
            print('wrong!!!!!')

        # get the user email and retrieve his/her info
        email = '{1}{0}{1}'.format(session['user_info'], "'")
        user_sql = """select * from buyers where buyers.email = """ + email
        email_with_enter = '{1}{0}{2}{1}'.format(session['user_info'], "'", "\r")
        credit_sql = """select * from credit where credit.owner_email = """ + email_with_enter
        name = query_buyer_info(user_sql)[0]['first_name'] + ' ' + query_buyer_info(user_sql)[0]['last_name']
        age = query_buyer_info(user_sql)[0]['age']
        gender = query_buyer_info(user_sql)[0]['gender']
        credit = query_buyer_info(credit_sql)[0]['credit_card_num'].split("-")[-1]
        credit_type = query_buyer_info(credit_sql)[0]['card_type']

        # address info
        sql4 = """select * from address where address_id = """
        sql5 = """select * from zipcode_info where zipcode = """
        homeid = '{1}{0}{1}'.format(query_buyer_info(user_sql)[0]['home_address_id'], "'")
        billid = '{1}{0}{1}'.format(query_buyer_info(user_sql)[0]['billing_address_id'].split("\r")[0], "'")
        homestreet_sql = query_buyer_info(sql4 + homeid)[0]
        home_zip = '{1}{0}{1}'.format(homestreet_sql['zipcode'], "'")
        billstreet_sql = query_buyer_info(sql4 + billid)[0]
        bill_zip = '{1}{0}{1}'.format(billstreet_sql['zipcode'], "'")
        home_zip_sql = query_buyer_info(sql5 + home_zip)[0]
        bill_zip_sql = query_buyer_info(sql5 + bill_zip)[0]
        homeadd = unquote(
            str(homestreet_sql['street_num']) + ' ' + homestreet_sql['street_name'] + ', ' + home_zip_sql[
                'city'] + ', ' + home_zip_sql['state_id'] + ', ' + home_zip_sql['zipcode'])
        billadd = str(billstreet_sql['street_num']) + ' ' + billstreet_sql['street_name'] + ', ' + \
                  bill_zip_sql['city'] + ', ' + bill_zip_sql['state_id'] + ', ' + bill_zip_sql['zipcode']

        # get all orders of the user
        order_sql = """select * from orders where buyer_email = """ + email
        order = query_buyer_info(order_sql)
        # if no orders, customize as no record
        if len(order) == 0:
            order = [{'transaction_id': 'No record', 'quantity': '', 'payment': ''}]

        # render the info page
        return render_template('info.html', email=session['user_info'], name=name, age=age, gender=gender,
                               credit=credit, credit_type=credit_type, home=homeadd, bill=billadd, order=order)


# config the route&method to search products
@app.route('/list/s', methods=['GET', "POST"])
def sousuosearch():
    if request.method == 'POST':
        # get the search field, and search for any products like the field
        soufield = '{1}{2}{0}{2}{1}'.format(request.form.get('sousuo1'), "'", "%")
        mohusousuo_sql = """select * from products where title like """ + soufield + """or product_name like """ + soufield + """or product_description like """ + soufield
        mohulist = query_buyer_info(mohusousuo_sql)

        # get the name, if noe seller
        s = format(request.form.get('s'))
        if s != 'Seller':
            # get the name
            email = '{1}{0}{1}'.format(session['user_info'], "'")
            user_sql = """select first_name from buyers where buyers.email = """ + email
            name = query_buyer_info(user_sql)[0]['first_name']
        # o/w keep seller
        else:
            name = 'Seller'

        cat = 'Search Result based on ' + request.form.get('sousuo1')

        # if there's no product listed when searching, return empty list page
        if len(mohulist) == 0:
            return render_template('emptylist.html', cat=cat, data=data, sub=sub, name=name)
        # o/w, normal listing
        else:
            return render_template('list.html', cat=cat, data=data, sub=sub, item=mohulist, name=name,
                                   len=len(mohulist))


# config the route&method to add products to shopping cart
@app.route('/detail/gwc', methods=['GET', "POST"])
def gouwuche():  # 已经有了2598 和2599 两个新商品 还有2600
    if request.method == 'POST':
        # get the buyer email, listing id, quantity, payment and the product name
        buyeremail = '{1}{0}{1}'.format(request.form.get('buyeremailgwc'), "'")
        lid = str(request.form.get('lidgwc'))
        quantity = str(request.form.get('quantitygwc'))
        pay = str(request.form.get('paygwc'))
        name = '{1}{0}{1}'.format(request.form.get('productnamegwc'), "'")

        # insert into the cart table
        cart_sql = """insert into cart (buyer_email, listing_id, quantity, payment, product_name) values (""" + buyeremail + """,""" + lid + """,""" + quantity + """,""" + pay + """,""" + name + """)"""
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(cart_sql)
            conn.commit()
            print('success')
        except:
            print('wrong!!!!!')

        # return the product detail page
        return detail1()


# config the route&method to remove products from shopping cart
@app.route('/info/g', methods=['GET', "POST"])
def shanchugouwuche():
    if request.method == 'POST':
        # get the cart id,
        cid = str(request.form.get('cid'))
        # delete that entity
        changed_sql = """delete from cart where cid =  """ + cid
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(changed_sql)
        conn.commit()

        # return the info page
        return info_page()


# config the route&method to remove products from shopping cart
@app.route('/info1/g', methods=['GET', "POST"])
def shanchugouwuche2():
    if request.method == 'POST':
        # get the cart id,
        cid = str(request.form.get('cid'))
        # delete that entity
        changepwd_sql = """delete from cart where cid =  """ + cid
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(changepwd_sql)
        conn.commit()

        # return the info page
        return info_page1()


# run
if __name__ == '__main__':
    app.run()


