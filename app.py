
import streamlit as st
import mysql.connector
import json

st.set_page_config(page_title="MiniShop", page_icon="🛍️", layout="wide")

# ---------- DATABASE CONNECTION ----------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Jerusha@08",
        database="minishop_db"
    )

# ---------- SESSION ----------
if "cart" not in st.session_state:
    st.session_state.cart = {}

# ---------- DATABASE FUNCTIONS ----------
def get_products():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return products

def get_orders():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return orders

def add_product(name, price, category, emoji, stock):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, price, category, emoji, stock) VALUES (%s,%s,%s,%s,%s)",
        (name, price, category, emoji, stock)
    )
    conn.commit()
    cursor.close()
    conn.close()

# ---------- STYLE ----------
st.markdown("""
<style>
.stApp { background-color: #f5f7fb; }
.hero {
    background: linear-gradient(120deg,#1e3a8a,#6366f1);
    padding: 30px;
    border-radius: 15px;
    color: white;
}
.hero h1 { color: white; }
</style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
st.sidebar.title("🛍️ MiniShop")
st.sidebar.caption("Your everyday shopping destination")

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Products", "Cart", "Checkout", "My Orders", "Admin"]
)

st.sidebar.divider()
st.sidebar.write(f"🛒 Cart items: {sum(st.session_state.cart.values())}")

# ---------- HOME ----------
if page == "Home":
    st.markdown("""
    <div class="hero">
        <h1>Welcome to MiniShop 🛍️</h1>
        <p>Discover products you'll love, all in one place.</p>
    </div>
    """, unsafe_allow_html=True)

    products = get_products()
    orders = get_orders()

    c1, c2, c3 = st.columns(3)
    c1.metric("Products", len(products))
    c2.metric("Cart Items", sum(st.session_state.cart.values()))
    c3.metric("Orders", len(orders))

    st.subheader("✨ Featured Products")
    cols = st.columns(3)
    for i, p in enumerate(products[:3]):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"## {p['emoji'] or '📦'}")
                st.subheader(p["name"])
                st.caption(p["category"])
                st.write(f"### ₹{p['price']}")
                st.caption(f"Stock: {p['stock']}")
                if p["stock"] > 0:
                    if st.button("🛒 Add to Cart", key=f"home_{p['id']}"):
                        st.session_state.cart[p["id"]] = (
                            st.session_state.cart.get(p["id"], 0) + 1
                        )
                        st.rerun()

# ---------- PRODUCTS ----------
elif page == "Products":
    st.title("🛍️ Product Catalog")
    products = get_products()

    search = st.text_input("🔍 Search products")
    categories = ["All"] + sorted(set(p["category"] for p in products))
    category = st.selectbox("Category", categories)

    filtered = [
        p for p in products
        if search.lower() in p["name"].lower()
        and (category == "All" or p["category"] == category)
    ]

    cols = st.columns(3)
    for i, p in enumerate(filtered):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"## {p['emoji'] or '📦'}")
                st.subheader(p["name"])
                st.caption(p["category"])
                st.markdown(f"### ₹{p['price']}")
                st.caption(f"Available: {p['stock']}")
                if p["stock"] > 0:
                    if st.button("Add to Cart", key=f"product_{p['id']}"):
                        current = st.session_state.cart.get(p["id"], 0)
                        if current < p["stock"]:
                            st.session_state.cart[p["id"]] = current + 1
                            st.toast("Added to cart!")
                            st.rerun()
                        else:
                            st.warning("Maximum available quantity reached.")
                else:
                    st.button("Out of Stock", disabled=True, key=f"out_{p['id']}")

    if not filtered:
        st.info("No products found.")

# ---------- CART ----------
elif page == "Cart":
    st.title("🛒 Your Cart")
    products = get_products()
    product_map = {p["id"]: p for p in products}

    for pid in list(st.session_state.cart):
        p = product_map.get(pid)
        if not p:
            del st.session_state.cart[pid]
            continue

        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 3, 1])
            col1.markdown(f"## {p['emoji'] or '📦'}")
            col2.write(f"**{p['name']}**")
            col2.write(f"₹{p['price']} each")
            qty = col3.number_input(
                "Quantity", min_value=1,
                max_value=max(1, p["stock"]),
                value=min(st.session_state.cart[pid], max(1, p["stock"])),
                key=f"qty_{pid}"
            )
            st.session_state.cart[pid] = qty
            if st.button("Remove", key=f"remove_{pid}"):
                del st.session_state.cart[pid]
                st.rerun()

    total = sum(
        product_map[pid]["price"] * qty
        for pid, qty in st.session_state.cart.items()
        if pid in product_map
    )
    st.divider()
    st.subheader(f"Total: ₹{total:,.2f}")
    if st.session_state.cart:
        st.info("Go to Checkout from the sidebar to place your order.")

# ---------- CHECKOUT ----------
elif page == "Checkout":
    st.title("📦 Checkout")
    products = get_products()
    product_map = {p["id"]: p for p in products}
    cart = st.session_state.cart

    if not cart:
        st.info("Your cart is empty.")
    else:
        total = sum(
            product_map[pid]["price"] * qty
            for pid, qty in cart.items() if pid in product_map
        )
        st.write(f"### Order Total: ₹{total:,.2f}")

        with st.form("checkout"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            address = st.text_area("Delivery Address")
            payment = st.selectbox("Payment", ["Cash on Delivery", "UPI (Demo)"])
            submit = st.form_submit_button("Place Order", type="primary")

        if submit:
            if not name.strip() or not email.strip() or not address.strip():
                st.error("Please complete all delivery details.")
            else:
                conn = get_db()
                cursor = conn.cursor()
                try:
                    conn.start_transaction()
                    items = []
                    for pid, qty in cart.items():
                        p = product_map.get(pid)
                        if not p:
                            raise ValueError("A product is no longer available.")
                        cursor.execute(
                            "UPDATE products SET stock = stock - %s WHERE id = %s AND stock >= %s",
                            (qty, pid, qty)
                        )
                        if cursor.rowcount != 1:
                            raise ValueError(f"Insufficient stock for {p['name']}.")
                        items.append({
                            "name": p["name"],
                            "qty": qty,
                            "price": float(p["price"])
                        })

                    cursor.execute("""
                        INSERT INTO orders
                        (customer_name, email, address, payment, items, total, status)
                        VALUES (%s,%s,%s,%s,%s,%s,'Pending')
                    """, (
                        name, email, address, payment,
                        json.dumps(items), total
                    ))
                    order_id = cursor.lastrowid
                    conn.commit()
                    st.session_state.cart = {}
                    st.success(f"Order #{order_id} placed successfully!")
                    st.balloons()
                except Exception as e:
                    conn.rollback()
                    st.error(str(e))
                finally:
                    cursor.close()
                    conn.close()

# ---------- MY ORDERS ----------
elif page == "My Orders":
    st.title("📦 Track Your Orders")
    email = st.text_input("Enter the email used at checkout")
    if email:
        orders = [
            o for o in get_orders()
            if o["email"].lower() == email.strip().lower()
        ]
        if not orders:
            st.info("No orders found for this email.")
        for order in orders:
            with st.expander(f"Order #{order['id']} — {order['status']}"):
                st.write(f"**Total:** ₹{order['total']}")
                st.write(f"**Status:** {order['status']}")
                st.write("**Items:**")
                items = order["items"]
                if isinstance(items, str):
                    items = json.loads(items)
                for item in items:
                    st.write(f"- {item['name']} × {item['qty']}")

# ---------- ADMIN ----------
elif page == "Admin":
    st.title("⚙️ Admin Dashboard")
    st.warning("Demo only: admin login and role protection are not implemented yet.")

    tab1, tab2, tab3 = st.tabs(
        ["Overview", "Add Product", "Manage Products & Orders"]
    )

    with tab1:
        products = get_products()
        orders = get_orders()
        c1, c2, c3 = st.columns(3)
        c1.metric("Products", len(products))
        c2.metric("Orders", len(orders))
        c3.metric("Sales", f"₹{sum(float(o['total']) for o in orders):,.2f}")

    with tab2:
        with st.form("add_product"):
            name = st.text_input("Product Name")
            price = st.number_input("Price", min_value=1.0)
            category = st.selectbox(
                "Category", ["Electronics", "Fashion", "Home", "Other"]
            )
            emoji = st.text_input("Emoji", "📦")
            stock = st.number_input("Stock", min_value=0, step=1)
            add = st.form_submit_button("Add Product")

        if add:
            if name.strip():
                add_product(name.strip(), price, category, emoji, stock)
                st.success("Product added!")
                st.rerun()
            else:
                st.error("Enter a product name.")

    with tab3:
        st.subheader("Products")
        for p in get_products():
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"{p['emoji'] or '📦'} {p['name']}")
            col2.write(f"₹{p['price']} | Stock: {p['stock']}")
            if col3.button("Delete", key=f"del_{p['id']}"):
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE id = %s", (p["id"],))
                conn.commit()
                cursor.close()
                conn.close()
                st.rerun()

        st.divider()
        st.subheader("Orders")
        for o in get_orders():
            with st.container(border=True):
                st.write(f"**Order #{o['id']}** — {o['customer_name']}")
                st.write(f"Total: ₹{o['total']}")
                statuses = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]
                status = st.selectbox(
                    "Status", statuses,
                    index=statuses.index(o["status"]),
                    key=f"status_{o['id']}"
                )
                if st.button("Update Status", key=f"update_{o['id']}"):
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE orders SET status = %s WHERE id = %s",
                        (status, o["id"])
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.success("Order status updated!")
                    st.rerun()
