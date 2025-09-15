import streamlit as st
import hashlib
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# --- MongoDB Connection ---
#    st.info("The UI is still loaded, but database actions won't work u")
# --- MongoDB Connection ---
uri = "mongodb+srv://root:TRAIPIHEFT@railway-cluster.qnvlez1.mongodb.net/?retryWrites=true&w=majority&appName=railway-cluster"

connection_ok = False
connection_error = ""
users_col = None
messages_col = None

try:
    client = MongoClient(uri, server_api=ServerApi('1'))
    client.admin.command('ping')  # test connection
    print("Pinged your deployment. You successfully connected to MongoDB!")

    db = client["railway_data"]
    users_col = db["users"]
    messages_col = db["messages"]

    connection_ok = True
except Exception as e:
    connection_error = str(e)

# ---------- Helper Functions ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(username, password):
    if users_col.find_one({"username": username}):
        return False
    users_col.insert_one({"username": username, "password": hash_password(password)})
    return True

def login_user(username, password):
    return users_col.find_one({"username": username, "password": hash_password(password)})

def route_message(department, content):
    messages_col.insert_one({
        "department": department,
        "content": content,
        "timestamp": datetime.now()
    })

def get_messages(department):
    return list(messages_col.find({"department": department}).sort("timestamp", -1))

def decide_department(text):
    text = text.lower()
    if "track" in text or "signal" in text:
        return "signals"
    elif "salary" in text or "leave" in text:
        return "hr"
    elif "repair" in text or "engine" in text:
        return "engineering"
    else:
        return "general"

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Railway Info Router", layout="centered")
st.title("Railway Department Info Router")

# Show DB connection status
if not connection_ok:
    st.error(f"Database connection failed:\n\n{connection_error}")
    st.info("The app UI is still loaded, but database actions will not work until the connection is fixed.")

menu = st.sidebar.selectbox("Menu", ["Login", "Signup", "Dashboard"])

# ---------- Signup ----------
if menu == "Signup":
    st.subheader("Create Account")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type="password")
    if st.button("Signup"):
        if not connection_ok:
            st.error("Database not connected. Cannot create account.")
        elif signup_user(new_user, new_password):
            st.success("Account created! Please login.")
        else:
            st.error("Username already exists.")

# ---------- Login ----------
elif menu == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if not connection_ok:
            st.error("Database not connected. Cannot log in.")
        else:
            user = login_user(username, password)
            if user:
                st.session_state.user = username
                st.success(f"Welcome {username}!")
            else:
                st.error("Invalid credentials.")

# ---------- Dashboard ----------
elif menu == "Dashboard":
    if st.session_state.get("user"):
        st.subheader(f"Dashboard for {st.session_state.user}")

        uploaded_file = st.file_uploader("Upload scanned file (text only)")
        manual_text = st.text_area("Or paste scanned text here")

        if st.button("Send"):
            if not connection_ok:
                st.error("Database not connected. Cannot send message.")
            else:
                if uploaded_file:
                    content = uploaded_file.read().decode("utf-8")
                else:
                    content = manual_text

                if content.strip():
                    dept = decide_department(content)
                    route_message(dept, content)
                    st.success(f"Message routed to {dept} department.")
                else:
                    st.warning("Please enter or upload some text.")

        st.subheader("Your Department Inbox")
        if not connection_ok:
            st.error("Database not connected. Cannot fetch messages.")
        else:
            messages = get_messages(st.session_state.user)
            if messages:
                for msg in messages:
                    st.write(f"📩 {msg['content']} \n🕒 {msg['timestamp']}")
            else:
                st.info("No messages yet.")
    else:
        st.warning("Please login first.")
