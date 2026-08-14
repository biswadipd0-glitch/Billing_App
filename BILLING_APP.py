import re

import mysql.connector
import pandas as pd
import streamlit as st
from mysql.connector import Error

# Import QR scanner from the separate Python file
import qr_code_scanner_feb_2026


# ---------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Retail Billing System",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 Retail Billing System")


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------
def get_connection():

    return mysql.connector.connect(

        host=st.secrets["MYSQL_HOST"],

        port=int(
            st.secrets["MYSQL_PORT"]
        ),

        user=st.secrets["MYSQL_USER"],

        password=st.secrets["MYSQL_PASSWORD"],

        database=st.secrets["MYSQL_DATABASE"]
    )


# ---------------------------------------------------------
# CUSTOMER RETRIEVAL
# ---------------------------------------------------------
def data_retrieve_customer(phone_number):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT CUST_ID, FULL_NAME, ADDRESS, PH_NUMBER
            FROM CUST_DETAILS
            WHERE PH_NUMBER = %s
        """

        cursor.execute(query, (phone_number,))
        return cursor.fetchone()

    except Error as error:
        st.error(f"Error retrieving customer: {error}")
        return None

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------------
# NEW CUSTOMER REGISTRATION
# ---------------------------------------------------------
def data_entry_customer(full_name, address, phone_number):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO CUST_DETAILS
            (FULL_NAME, ADDRESS, PH_NUMBER)
            VALUES (%s, %s, %s)
        """

        data = (
            full_name.strip().upper(),
            address.strip().upper(),
            phone_number
        )

        cursor.execute(query, data)
        connection.commit()

        return cursor.lastrowid

    except Error as error:
        if connection:
            connection.rollback()

        st.error(f"Error registering customer: {error}")
        return None

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------------
# PRODUCT RETRIEVAL
# ---------------------------------------------------------
def data_retrieve_product(product_id):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT P_ID, P_NAME, P_PRICE, STOCK_ON_HAND
            FROM PRODUCT_DETAILS
            WHERE P_ID = %s
        """

        cursor.execute(query, (product_id,))
        return cursor.fetchone()

    except Error as error:
        st.error(f"Error retrieving product: {error}")
        return None

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------------
# FINAL BILL CREATION
# ---------------------------------------------------------
def create_final_bill(customer, cart):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        total_bill_value = sum(
            float(item["PRODUCT_PRICE"]) * int(item["QUANTITY"])
            for item in cart
        )

        summary_query = """
            INSERT INTO BILL_SUMMARY_TABLE
            (C_ID, C_NAME, TOTAL_BILL_VALUE)
            VALUES (%s, %s, %s)
        """

        cursor.execute(
            summary_query,
            (
                customer["CUST_ID"],
                customer["FULL_NAME"],
                total_bill_value
            )
        )

        bill_id = cursor.lastrowid

        details_query = """
            INSERT INTO BILL_DETAILS_TB
            (BILL_ID, C_ID, P_ID, P_NAME, QUANTITY)
            VALUES (%s, %s, %s, %s, %s)
        """

        bill_records = []

        for item in cart:
            bill_records.append(
                (
                    bill_id,
                    customer["CUST_ID"],
                    item["P_ID"],
                    item["P_NAME"],
                    item["QUANTITY"]
                )
            )

        cursor.executemany(details_query, bill_records)

        connection.commit()

        return bill_id, total_bill_value

    except Error as error:
        if connection:
            connection.rollback()

        st.error(f"Error creating bill: {error}")
        return None, None

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
if "customer" not in st.session_state:
    st.session_state.customer = None

if "customer_not_found" not in st.session_state:
    st.session_state.customer_not_found = False

if "searched_phone_number" not in st.session_state:
    st.session_state.searched_phone_number = ""

if "cart" not in st.session_state:
    st.session_state.cart = []

if "scanned_product" not in st.session_state:
    st.session_state.scanned_product = None

if "last_bill" not in st.session_state:
    st.session_state.last_bill = None


# ---------------------------------------------------------
# MYSQL CONNECTION TEST
# ---------------------------------------------------------
try:
    test_connection = get_connection()

    if test_connection.is_connected():
        st.success("MySQL localhost connected successfully.")

    test_connection.close()

except Error as error:
    st.error(f"MySQL connection failed: {error}")
    st.stop()


# ---------------------------------------------------------
# CUSTOMER SEARCH
# ---------------------------------------------------------
if st.session_state.customer is None:

    st.subheader("Customer Identification")

    with st.form("customer_search_form"):

        phone_number = st.text_input(
            "Enter customer phone number",
            max_chars=15
        )

        search_button = st.form_submit_button(
            "Search Customer",
            use_container_width=True
        )

    if search_button:

        cleaned_phone_number = re.sub(
            r"\D",
            "",
            phone_number
        )

        if not cleaned_phone_number:
            st.warning("Please enter a valid phone number.")

        else:
            customer = data_retrieve_customer(
                cleaned_phone_number
            )

            st.session_state.searched_phone_number = (
                cleaned_phone_number
            )

            if customer:
                st.session_state.customer = customer
                st.session_state.customer_not_found = False
                st.rerun()

            else:
                st.session_state.customer_not_found = True

                st.warning(
                    "Customer not found. Please register the customer."
                )


# ---------------------------------------------------------
# NEW CUSTOMER REGISTRATION
# ---------------------------------------------------------
if (
    st.session_state.customer is None
    and st.session_state.customer_not_found
):

    st.subheader("New Customer Registration")

    with st.form("customer_registration_form"):

        full_name = st.text_input(
            "Customer full name"
        )

        address = st.text_area(
            "Customer address"
        )

        phone_number = st.text_input(
            "Phone number",
            value=st.session_state.searched_phone_number,
            disabled=True
        )

        register_button = st.form_submit_button(
            "Register Customer",
            use_container_width=True
        )

    if register_button:

        if not full_name.strip():
            st.warning("Please enter the customer name.")

        elif not address.strip():
            st.warning("Please enter the customer address.")

        else:
            customer_id = data_entry_customer(
                full_name,
                address,
                st.session_state.searched_phone_number
            )

            if customer_id:
                customer = data_retrieve_customer(
                    st.session_state.searched_phone_number
                )

                if customer:
                    st.session_state.customer = customer
                    st.session_state.customer_not_found = False

                    st.success(
                        "Customer registration successful."
                    )

                    st.rerun()


# ---------------------------------------------------------
# BILLING SECTION
# ---------------------------------------------------------
if st.session_state.customer:

    customer = st.session_state.customer

    customer_column, change_column = st.columns([4, 1])

    with customer_column:

        st.subheader("Customer Details")

        st.write(
            f"**Customer ID:** {customer['CUST_ID']}"
        )

        st.write(
            f"**Customer Name:** {customer['FULL_NAME']}"
        )

        st.write(
            f"**Phone Number:** {customer['PH_NUMBER']}"
        )

        st.write(
            f"**Address:** {customer['ADDRESS']}"
        )

    with change_column:

        if st.button(
            "Change Customer",
            use_container_width=True
        ):
            st.session_state.customer = None
            st.session_state.customer_not_found = False
            st.session_state.searched_phone_number = ""
            st.session_state.cart = []
            st.session_state.scanned_product = None
            st.session_state.last_bill = None

            st.rerun()

    st.divider()

    scanner_column, product_column = st.columns(2)

    # -----------------------------------------------------
    # QR SCANNER
    # -----------------------------------------------------
    with scanner_column:

        st.subheader("Product QR Scanner")

        st.info(
            "Click the button below. The OpenCV camera window "
            "will open and remain active until a QR code is scanned."
        )

        if st.button(
            "Open Camera and Scan QR",
            type="primary",
            use_container_width=True
        ):

            try:
                product_id = (
                    qr_code_scanner_feb_2026.qr_code_scanner()
                )

                if product_id:
                    product = data_retrieve_product(
                        product_id
                    )

                    if product:
                        st.session_state.scanned_product = product

                        st.success(
                            f"Product scanned: {product['P_NAME']}"
                        )

                    else:
                        st.session_state.scanned_product = None

                        st.error(
                            f"Product ID {product_id} was not found."
                        )

                else:
                    st.warning(
                        "No product QR code was scanned."
                    )

            except Exception as error:
                st.error(
                    f"QR scanner error: {error}"
                )

    # -----------------------------------------------------
    # SCANNED PRODUCT DETAILS
    # -----------------------------------------------------
    with product_column:

        st.subheader("Scanned Product")

        if st.session_state.scanned_product:

            product = st.session_state.scanned_product

            st.write(
                f"**Product ID:** {product['P_ID']}"
            )

            st.write(
                f"**Product Name:** {product['P_NAME']}"
            )

            st.write(
                f"**Price:** ₹{float(product['P_PRICE']):,.2f}"
            )

            st.write(
                f"**Available Stock:** {product['STOCK_ON_HAND']}"
            )

            quantity = st.number_input(
                "Enter quantity",
                min_value=1,
                max_value=int(product["STOCK_ON_HAND"]),
                value=1,
                step=1
            )

            if st.button(
                "Add Product to Bill",
                use_container_width=True
            ):

                existing_product = next(
                    (
                        item
                        for item in st.session_state.cart
                        if item["P_ID"] == product["P_ID"]
                    ),
                    None
                )

                if existing_product:

                    new_quantity = (
                        existing_product["QUANTITY"]
                        + int(quantity)
                    )

                    if new_quantity > int(
                        product["STOCK_ON_HAND"]
                    ):
                        st.warning(
                            "Requested quantity exceeds available stock."
                        )

                    else:
                        existing_product["QUANTITY"] = (
                            new_quantity
                        )

                        existing_product["TOTAL"] = (
                            float(
                                existing_product["PRODUCT_PRICE"]
                            )
                            * new_quantity
                        )

                        st.session_state.scanned_product = None

                        st.success(
                            "Product quantity updated."
                        )

                        st.rerun()

                else:

                    st.session_state.cart.append(
                        {
                            "P_ID": product["P_ID"],
                            "P_NAME": product["P_NAME"],
                            "PRODUCT_PRICE": float(
                                product["P_PRICE"]
                            ),
                            "QUANTITY": int(quantity),
                            "TOTAL": (
                                float(product["P_PRICE"])
                                * int(quantity)
                            )
                        }
                    )

                    st.session_state.scanned_product = None

                    st.success(
                        "Product added to the bill."
                    )

                    st.rerun()

        else:
            st.info(
                "Scan a product QR code to view product details."
            )

    st.divider()

    # -----------------------------------------------------
    # CURRENT CART
    # -----------------------------------------------------
    st.subheader("Current Bill")

    if st.session_state.cart:

        cart_dataframe = pd.DataFrame(
            st.session_state.cart
        )

        display_dataframe = cart_dataframe.rename(
            columns={
                "P_ID": "Product ID",
                "P_NAME": "Product Name",
                "PRODUCT_PRICE": "Price",
                "QUANTITY": "Quantity",
                "TOTAL": "Total"
            }
        )

        st.dataframe(
            display_dataframe,
            use_container_width=True,
            hide_index=True
        )

        total_bill_value = sum(
            item["TOTAL"]
            for item in st.session_state.cart
        )

        st.metric(
            "Total Bill Value",
            f"₹{total_bill_value:,.2f}"
        )

        remove_product_id = st.selectbox(
            "Select product to remove",
            options=[
                item["P_ID"]
                for item in st.session_state.cart
            ],
            format_func=lambda selected_id: next(
                (
                    f"{item['P_NAME']} - Product ID {item['P_ID']}"
                    for item in st.session_state.cart
                    if item["P_ID"] == selected_id
                ),
                str(selected_id)
            )
        )

        remove_column, clear_column = st.columns(2)

        with remove_column:

            if st.button(
                "Remove Selected Product",
                use_container_width=True
            ):
                st.session_state.cart = [
                    item
                    for item in st.session_state.cart
                    if item["P_ID"] != remove_product_id
                ]

                st.rerun()

        with clear_column:

            if st.button(
                "Clear Complete Bill",
                use_container_width=True
            ):
                st.session_state.cart = []
                st.session_state.scanned_product = None

                st.rerun()

        if st.button(
            "Finalize Bill",
            type="primary",
            use_container_width=True
        ):

            bill_id, final_bill_value = create_final_bill(
                customer,
                st.session_state.cart
            )

            if bill_id:

                st.session_state.last_bill = {
                    "BILL_ID": bill_id,
                    "CUSTOMER_NAME": customer["FULL_NAME"],
                    "TOTAL_BILL_VALUE": final_bill_value
                }

                st.session_state.cart = []
                st.session_state.scanned_product = None

                st.rerun()

    else:
        st.info(
            "No products have been added to the bill."
        )


# ---------------------------------------------------------
# GENERATED BILL
# ---------------------------------------------------------
if st.session_state.last_bill:

    st.divider()
    st.subheader("Bill Generated Successfully")

    st.success(
        f"""
        Bill ID: {st.session_state.last_bill['BILL_ID']}

        Customer: {st.session_state.last_bill['CUSTOMER_NAME']}

        Total Bill Value:
        ₹{st.session_state.last_bill['TOTAL_BILL_VALUE']:,.2f}
        """
    )

    if st.button(
        "Start New Bill",
        use_container_width=True
    ):
        st.session_state.customer = None
        st.session_state.customer_not_found = False
        st.session_state.searched_phone_number = ""
        st.session_state.cart = []
        st.session_state.scanned_product = None
        st.session_state.last_bill = None

        st.rerun()
