from datetime import timedelta, datetime
import pandas as pd
import streamlit as st
from sqlalchemy.sql import text

st.title('OrderSense - Order Management System')

# connect to database
conn = st.experimental_connection("sqlite_db", type="sql")

with conn.session as s:
    st.markdown(f"Note that `s` is a `{type(s)}`")

    s.execute(text('CREATE TABLE IF NOT EXISTS orders (order_id INTEGER PRIMARY KEY, order_date TEXT, order_time TEXT, order_type TEXT, order_table INTEGER, order_name TEXT);'))

    s.execute(text('CREATE TABLE IF NOT EXISTS order_items (item_id INTEGER, item TEXT, quantity INTEGER, price DECIMAL, order_id INTEGER, FOREIGN KEY (order_id) REFERENCES orders(order_id));'))

    s.commit()
    s.close()

# tabs for the app
tab1, tab2, tab3 = st.tabs(["Take the order", "Order List", "Weekly Report"])

# tab1 - take the order
tab1.title('Take the order')
tab1.subheader('Please enter the order details below')

# order details
order_date = tab1.date_input('Order Date', pd.to_datetime('today', utc=True))
order_date = order_date.strftime('%Y-%m-%d')
order_time = tab1.time_input('Order Time', pd.to_datetime('now', utc=True))
order_time = order_time.strftime('%H:%M:%S')
order_type = tab1.selectbox('Order Type', ['Dine In', 'Take Away', 'Delivery'])
order_table = tab1.number_input(
    'Table Number', min_value=1, max_value=10, value=1)
order_name = tab1.text_input('Customer Name')

# order items
items = {'Coffee': 3.5, 'Tea': 3.5, 'Burger': 10, 'Pizza': 12, 'Pasta': 12,
         'Salad': 10, 'Sandwich': 8, 'Steak': 15, 'Soup': 8, 'Sushi': 12, 'Wings': 10}

item = tab1.selectbox('Item', items.items(
), format_func=lambda x: f'{x[0]} ------------------ ${x[1]}')
quantity = tab1.number_input('Quantity', min_value=1, max_value=10, value=1)
add_item = tab1.button('Add Item')

with conn.session as s:
    latest_order_id = s.execute(
        'SELECT MAX(order_id) FROM orders').fetchone()[0]
    if latest_order_id is None:
        order_id = 1
    else:
        order_id = latest_order_id + 1

    if add_item:
        s.execute(
            text('INSERT INTO order_items (item, quantity, price, order_id) VALUES (:item, :quantity, :price, :order_id);'),
            params=dict(item=item[0], quantity=quantity,
                        price=item[1], order_id=order_id)
        )
        s.commit()

        query = 'select * from order_items where order_id='+str(order_id)

        order = conn.query(query)
        tab1.dataframe(order)

# order summary
submit = tab1.button('Submit')
if submit:
    s.execute(
        text('INSERT INTO orders (order_date, order_time, order_type, order_table, order_name) VALUES (:order_date, :order_time, :order_type, :order_table, :order_name);'),
        params=dict(order_date=order_date, order_time=order_time,
                    order_type=order_type, order_table=order_table, order_name=order_name)
    )
    s.commit()
    s.close()
    tab1.success('Order submitted successfully!')

# tab2 - order list
tab2.title('Order List')
order = conn.query('select * from orders')
refresh_list = tab2.button('Refresh List')
if refresh_list:
    order = conn.query('select * from orders')
tab2.dataframe(order)

# tab3 - weekly report
tab3.title('Weekly Report')
weekly_report = conn.query('select * from orders')
data = pd.DataFrame(weekly_report)
data = data.groupby(['order_date']).size().reset_index(name='order_table')
data['order_date'] = pd.to_datetime(data['order_date'])
data['order_date'] = data['order_date'].dt.strftime('%Y-%m-%d')
data = data.rename(columns={'order_table': 'order_count'})
refresh_chart = tab3.button('Refresh Charts')
if refresh_chart:
    data = pd.DataFrame(weekly_report)
    data = data.groupby(['order_date']).size().reset_index(name='order_table')
    data['order_date'] = pd.to_datetime(data['order_date'])
    print(data['order_date'])
    data['order_date'] = data['order_date'].dt.strftime('%Y-%m-%d')
    data = data.rename(columns={'order_table': 'order_count'})
tab3.bar_chart(data=data, x='order_date', y='order_count', )
