# app.py
import streamlit as st
import validators
import sqlite3
from pathlib import Path
import random

# Constants
TOTAL_COMBINATIONS = 16 ** 7  # 268,435,456

# Set page config as the first command
st.set_page_config(
    page_title="🔗 URL Shortener",
    page_icon="🔗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize SQLite database
@st.cache_resource
def init_db():
    DB_PATH = 'url_shortener.db'
    db_exists = Path(DB_PATH).is_file()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)  # Fix for SQLite threading issue
    cursor = conn.cursor()
    if not db_exists:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                short_code TEXT PRIMARY KEY,
                original_url TEXT UNIQUE NOT NULL,
                click_count INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
    return conn, cursor

# Generate a unique short code
def generate_short_code(cursor, length=7):
    characters = '0123456789abcdef'
    while True:
        short_code = ''.join(random.choices(characters, k=length))
        cursor.execute('SELECT short_code FROM urls WHERE short_code = ?', (short_code,))
        result = cursor.fetchone()
        if not result:
            return short_code

# Generate 30 million unique hex codes
def generate_hex_codes():
    characters = '0123456789abcdef'
    hex_codes = set()  # Use a set to avoid duplicates
    while len(hex_codes) < 30000000:
        hex_code = ''.join(random.choices(characters, k=7))
        hex_codes.add(hex_code)
    return list(hex_codes)

# Main application logic
def main():
    conn, cursor = init_db()

    # Set the base URL to the deployed app's URL
    BASE_URL = "https://url-shortener-from-vignesh.streamlit.app/"  # Replace this with your actual deployed app URL
    
    # Centered menu with radio buttons instead of sidebar
    st.markdown("<h1 style='text-align: center;'>🔗 URL Shortener</h1>", unsafe_allow_html=True)
    
    menu = st.radio(
        "",
        ["Home", "Retrieve", "Generate"],
        horizontal=True,
        index=0,
        key="main_menu"
    )
    
    # Home page: URL Shortener
    if menu == "Home":
        st.title("🔗 URL Shortener")
        with st.form("shorten_form"):
            original_url = st.text_input("Enter the URL to shorten:")
            submitted = st.form_submit_button("Shorten URL")

        if submitted:
            if not original_url:
                st.error("Please enter a URL.")
            elif not validators.url(original_url):
                st.error("Invalid URL. Please enter a valid URL (e.g., https://example.com).")
            else:
                # Check if the URL is already shortened
                cursor.execute('SELECT short_code FROM urls WHERE original_url = ?', (original_url,))
                result = cursor.fetchone()

                if result:
                    short_code = result[0]
                    short_url = f"{BASE_URL}/?c={short_code}"
                    st.info(f"URL already shortened: {short_url}")
                else:
                    # Generate new short code and store it
                    short_code = generate_short_code(cursor)
                    cursor.execute('INSERT INTO urls (short_code, original_url) VALUES (?, ?)', (short_code, original_url))
                    conn.commit()
                    short_url = f"{BASE_URL}/?c={short_code}"
                    st.success(f"Short URL created: {short_url}")

        # Add a section explaining the formula used for 7-character hex codes
        st.markdown("## How We Calculate 7-Character Hex Codes")
        st.markdown("""
        In our URL shortener, we generate 7-character hexadecimal codes. A hexadecimal character can be any of the following 16 values:

        ```
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, a, b, c, d, e, f
        ```

        The formula to calculate the total number of possible combinations for 7-character hex codes is:

        \[
        16^7 = 268,435,456
        \]

        This means there are a total of **268,435,456** unique combinations of 7-character hexadecimal codes. This ensures that we can create millions of unique short codes while maintaining a high level of uniqueness.
        """, unsafe_allow_html=True)

    # Retrieve page: Display existing URL mappings
    elif menu == "Retrieve":
        st.title("🔍 Retrieve URL Mappings")
        cursor.execute('SELECT short_code, original_url FROM urls')
        rows = cursor.fetchall()

        if rows:
            for row in rows:
                short_url = f"{BASE_URL}/?c={row[0]}"
                original_url = row[1]
                st.write(f"🔗 [Short URL: {short_url}] | Original URL: {original_url}")
        else:
            st.info("No URL mappings found.")

    # Generate page: Generate 30 million unique hex codes
    elif menu == "Generate":
        st.title("⚙️ Generate 30 Million Hex Codes")
        if st.button("Generate Hex Codes"):
            st.info("Generating 30 million hex codes, this may take a while...")
            hex_codes = generate_hex_codes()
            st.success(f"Successfully generated 30 million unique hex codes.")
            st.write(f"Here are the first 10 generated codes:")
            st.write(hex_codes[:10])

if __name__ == "__main__":
    main()

