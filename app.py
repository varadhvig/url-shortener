import streamlit as st
import validators
import sqlite3
from pathlib import Path
import random
import os

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
    cursor.execute('PRAGMA journal_mode=WAL')  # Enable WAL mode for concurrent access
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

# Delete the database file (and clear cache)
def delete_database():
    DB_PATH = 'url_shortener.db'
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        st.cache_resource.clear()  # Clear the cache when deleting the database
        st.success("Database deleted successfully.")
    else:
        st.error("Database file not found.")

# Main application logic
def main():
    conn, cursor = init_db()

    # Set the base URL to the deployed app's URL
    BASE_URL = "https://url-shortener-from-vignesh.streamlit.app/"  # Replace this with your actual deployed app URL

    # Check for short code in the query parameters
    query_params = st.experimental_get_query_params()  # You can replace this with st.query_params after 2024-04-11
    if 'c' in query_params:
        short_code = query_params['c'][0]

        # Retrieve the original URL based on the short code
        cursor.execute('SELECT original_url FROM urls WHERE short_code = ?', (short_code,))
        result = cursor.fetchone()

        if result:
            original_url = result[0]
            # Perform the client-side redirection using meta refresh
            st.components.v1.html(f"""
                <meta http-equiv="refresh" content="0; url={original_url}" />
            """, height=0)
            return  # End the execution after redirection

    # Centered menu with radio buttons instead of sidebar
    st.markdown("<h1 style='text-align: center;'>🔗 URL Shortener</h1>", unsafe_allow_html=True)

    menu = st.radio(
        "",
        ["Home", "Retrieve", "Generate", "Delete Database"],
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
        In our URL shortener, I generate 7-character hexadecimal codes instead of 4. A hexadecimal character can be any of the following 16 values:

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
            hex_codes = set()  # Generate 30 million hex codes without storing them
            while len(hex_codes) < 30000000:
                hex_code = ''.join(random.choices('0123456789abcdef', k=7))
                hex_codes.add(hex_code)
            st.success(f"Successfully generated 30 million unique hex codes.")
            st.write(f"Here are the first 10 generated codes:")
            st.write(list(hex_codes)[:10])

    # Delete Database page: Allow user to delete the database
    elif menu == "Delete Database":
        st.title("🗑️ Delete Database")
        if st.button("Delete Database"):
            delete_database()

if __name__ == "__main__":
    main()
