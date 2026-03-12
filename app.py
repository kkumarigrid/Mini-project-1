import streamlit as st
from dotenv import load_dotenv
import os



from db import db, get_connection
from auth import signup, login
from scraper import Scraper

load_dotenv()

APP_TITLE = os.getenv("APP_TITLE", "Cooking Recipe Database")
CUISINES  = ["Indian", "Italian", "Chinese", "Mexican", "Mediterranean", "Global"]
DIETS     = ["Veg", "Non-Veg", "Vegan", "Keto", "Paleo"]

st.set_page_config(page_title=APP_TITLE, page_icon="🍲", layout="wide")
st.title(f"🍲 {APP_TITLE}")

if "user" not in st.session_state:
    st.session_state.user = None

menu = ["Login", "Signup", "Browse Recipes", "Add Recipe", "Seed Database"]

if st.session_state.user:
    menu.append("Manage Recipes")
    st.sidebar.success(f"👤 {st.session_state.user['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()
else:
    st.sidebar.info("👤 Not logged in")

choice = st.sidebar.selectbox("Menu", menu)

# ── LOGIN ─────────────────────────────────────────────────────────────────────
if choice == "Login":
    st.subheader("🔐 Login")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        user, message = login(u, p)
        if user:
            st.session_state.user = user
            st.success(message)
            st.rerun()
        else:
            st.error(message)

# ── SIGNUP ────────────────────────────────────────────────────────────────────
elif choice == "Signup":
    st.subheader("📝 Signup")
    with st.form("signup_form"):
        u  = st.text_input("Create Username")
        p  = st.text_input("Create Password",  type="password")
        p2 = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Signup")
    if submitted:
        if p != p2:
            st.error("Passwords do not match.")
        else:
            success, message = signup(u, p)
            if success:
                st.success(message)
            else:
                st.error(message)

# ── ADD RECIPE ────────────────────────────────────────────────────────────────
elif choice == "Add Recipe":
    st.subheader("➕ Add Recipe")
    if not st.session_state.user:
        st.warning("Login first to add recipes.")
    else:
        with st.form("add_recipe_form"):
            col1, col2 = st.columns(2)
            with col1:
                name    = st.text_input("Recipe Name")
                cuisine = st.selectbox("Cuisine", CUISINES)
                diet    = st.selectbox("Diet", DIETS)
            with col2:
                time     = st.number_input("Cooking Time (mins)", min_value=1, step=1)
                calories = st.number_input("Calories",    min_value=0, step=10)
                protein  = st.number_input("Protein (g)", min_value=0, step=1)
                carbs    = st.number_input("Carbs (g)",   min_value=0, step=1)
                fat      = st.number_input("Fat (g)",     min_value=0, step=1)
            ingredients = st.text_area("Ingredients (comma separated)")
            steps       = st.text_area("Steps (comma separated)")
            submitted   = st.form_submit_button("Add Recipe")

        if submitted:
            if not name.strip():
                st.error("Recipe name cannot be empty.")
            elif not ingredients.strip():
                st.error("Please add at least one ingredient.")
            elif not steps.strip():
                st.error("Please add at least one step.")
            else:
                with db.get_cursor() as cur:
                    cur.execute(
                        """INSERT INTO recipes
                        (name, cuisine, diet, cooking_time, calories, protein, carbs, fat, created_by)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                        (name.strip(), cuisine, diet, time, calories, protein, carbs, fat, st.session_state.user["id"])
                    )
                    recipe_id = cur.fetchone()["id"]
                    for ing in ingredients.split(","):
                        if ing.strip():
                            cur.execute(
                                "INSERT INTO ingredients (recipe_id, ingredient) VALUES (%s, %s)",
                                (recipe_id, ing.strip())
                            )
                    for step in steps.split(","):
                        if step.strip():
                            cur.execute(
                                "INSERT INTO steps (recipe_id, step) VALUES (%s, %s)",
                                (recipe_id, step.strip())
                            )
                st.success(f"✅ Recipe '{name}' added!")

# ── BROWSE & SEARCH ───────────────────────────────────────────────────────────
elif choice == "Browse Recipes":
    st.subheader("🔍 Browse Recipes")

    col1, col2, col3 = st.columns([3, 1.5, 1.5])
    with col1:
        search = st.text_input("Search Recipe")
    with col2:
        cuisine_filter = st.selectbox("Cuisine", ["All"] + CUISINES)
    with col3:
        diet_filter = st.selectbox("Diet", ["All"] + DIETS)

    query  = """SELECT r.*, ROUND(AVG(rv.rating), 1) AS avg_rating
                FROM recipes r
                LEFT JOIN reviews rv ON r.id = rv.recipe_id
                WHERE 1=1"""
    params = []

    if search:
        query += " AND r.name ILIKE %s"
        params.append(f"%{search}%")
    if cuisine_filter != "All":
        query += " AND r.cuisine = %s"
        params.append(cuisine_filter)
    if diet_filter != "All":
        query += " AND r.diet = %s"
        params.append(diet_filter)

    query += " GROUP BY r.id ORDER BY r.id DESC"

    with db.get_cursor() as cur:
        cur.execute(query, params)
        recipes = cur.fetchall()

    st.caption(f"{len(recipes)} recipe(s) found")

    if not recipes:
        st.info("No recipes found. Seed the database first from the sidebar.")

    for r in recipes:
        r = dict(r)
        stars = f"⭐ {r['avg_rating']}" if r["avg_rating"] else "No ratings yet"

        st.markdown(
            f"""<div style="border:1px solid #ddd; border-radius:10px;
                padding:14px 18px; margin-bottom:10px; background:#fafafa;">
                <b>🍽️ {r['name']}</b> &nbsp;|&nbsp;
                🌍 {r['cuisine']} &nbsp;|&nbsp; 🥗 {r['diet']} &nbsp;|&nbsp;
                ⏱️ {r['cooking_time']} min &nbsp;|&nbsp;
                🔥 {r['calories']} kcal &nbsp;|&nbsp; {stars}
                </div>""",
            unsafe_allow_html=True
        )

        with st.expander(f"View — {r['name']}"):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🔥 Calories", f"{r['calories']} kcal")
            col2.metric("💪 Protein",  f"{r['protein']}g")
            col3.metric("🌾 Carbs",    f"{r['carbs']}g")
            col4.metric("🧈 Fat",      f"{r['fat']}g")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🧂 Ingredients**")
                with db.get_cursor() as cur:
                    cur.execute(
                        "SELECT ingredient FROM ingredients WHERE recipe_id = %s", (r["id"],)
                    )
                    for ing in cur.fetchall():
                        st.write(f"• {ing['ingredient']}")
            with col2:
                st.markdown("**👨‍🍳 Steps**")
                with db.get_cursor() as cur:
                    cur.execute(
                        "SELECT step FROM steps WHERE recipe_id = %s ORDER BY id", (r["id"],)
                    )
                    for i, step in enumerate(cur.fetchall(), 1):
                        st.write(f"**{i}.** {step['step']}")
            
            # Like and Save
            like_count = 0
            with db.get_cursor() as cur:
                cur.execute("SELECT COUNT(*) AS total FROM likes WHERE recipe_id=%s", (r["id"],))
                like_count = cur.fetchone()["total"]

            if st.session_state.user:
                user_id = st.session_state.user["id"]
                col1, col2 = st.columns(2)

                with col1:
                    if st.button(f"❤️ Like ({like_count})", key=f"like_{r['id']}"):
                        try:
                            with db.get_cursor() as cur:
                                cur.execute(
                                    "INSERT INTO likes (user_id, recipe_id) VALUES (%s, %s)",
                                    (user_id, r["id"])
                                )
                            st.success("Liked!")
                        except:
                            st.info("Already liked!")

                with col2:
                    if st.button("💾 Save", key=f"save_{r['id']}"):
                        try:
                            with db.get_cursor() as cur:
                                cur.execute(
                                    "INSERT INTO saved_recipes (user_id, recipe_id) VALUES (%s, %s)",
                                    (user_id, r["id"])
                                )
                            st.success("Saved!")
                        except:
                            st.info("Already saved!")
            else:
                st.info("Login to like and save recipes.")
                
            st.markdown("**⭐ Reviews**")
            with db.get_cursor() as cur:
                cur.execute(
                    """SELECT rv.rating, rv.comment, u.username
                       FROM reviews rv
                       JOIN users u ON rv.user_id = u.id
                       WHERE rv.recipe_id = %s ORDER BY rv.id DESC""",
                    (r["id"],)
                )
                reviews = cur.fetchall()

            if reviews:
                for rev in reviews:
                    st.write(f"**{rev['username']}** — {'⭐' * rev['rating']}")
                    st.caption(rev["comment"])
            else:
                st.caption("No reviews yet.")

            if st.session_state.user:
                st.markdown("**📝 Leave a Review**")
                with st.form(f"review_{r['id']}"):
                    rating  = st.slider("Rating", 1, 5, 3)
                    comment = st.text_input("Comment")
                    review_submitted = st.form_submit_button("Submit")
                if review_submitted:
                    if not comment.strip():
                        st.error("Comment cannot be empty.")
                    else:
                        with db.get_cursor() as cur:
                            cur.execute(
                                """INSERT INTO reviews (recipe_id, user_id, rating, comment)
                                   VALUES (%s, %s, %s, %s)""",
                                (r["id"], st.session_state.user["id"], rating, comment.strip())
                            )
                        st.success("Review added!")
                        st.rerun()
            else:
                st.info("Login to leave a review.")

            st.markdown("**💡 Suggested Recipes**")
            with db.get_cursor() as cur:
                cur.execute(
                    """SELECT name FROM recipes
                       WHERE cuisine = %s AND diet = %s AND id != %s
                       LIMIT 3""",
                    (r["cuisine"], r["diet"], r["id"])
                )
                for rec in cur.fetchall():
                    st.write("👉", rec["name"])

# ── MANAGE RECIPES ────────────────────────────────────────────────────────────
elif choice == "Manage Recipes":
    st.subheader("⚙️ Manage Recipes")
    if not st.session_state.user:
        st.warning("Please login first.")
    else:
        user_id = st.session_state.user["id"]

        st.markdown("### ❤️ Liked Recipes")
        with db.get_cursor() as cur:
            cur.execute(
                """SELECT r.* FROM recipes r
                   JOIN likes l ON r.id = l.recipe_id
                   WHERE l.user_id = %s ORDER BY r.id DESC""",
                (user_id,)
            )
            liked = cur.fetchall()

        if not liked:
            st.caption("No liked recipes yet.")
        for r in liked:
            r = dict(r)
            col1, col2 = st.columns([4, 1])
            col1.write(f"🍽️ {r['name']} — {r['cuisine']} · {r['diet']}")
            with col2:
                if st.button("💔 Unlike", key=f"unlike_{r['id']}"):
                    with db.get_cursor() as cur:
                        cur.execute(
                            "DELETE FROM likes WHERE user_id=%s AND recipe_id=%s",
                            (user_id, r["id"])
                        )
                    st.rerun()

        st.markdown("---")
        st.markdown("### 💾 Saved Recipes")
        with db.get_cursor() as cur:
            cur.execute(
                """SELECT r.* FROM recipes r
                   JOIN saved_recipes s ON r.id = s.recipe_id
                   WHERE s.user_id = %s ORDER BY r.id DESC""",
                (user_id,)
            )
            saved = cur.fetchall()

        if not saved:
            st.caption("No saved recipes yet.")
        for r in saved:
            r = dict(r)
            col1, col2 = st.columns([4, 1])
            col1.write(f"🍽️ {r['name']} — {r['cuisine']} · {r['diet']}")
            with col2:
                if st.button("🗑️ Unsave", key=f"unsave_{r['id']}"):
                    with db.get_cursor() as cur:
                        cur.execute(
                            "DELETE FROM saved_recipes WHERE user_id=%s AND recipe_id=%s",
                            (user_id, r["id"])
                        )
                    st.rerun()

        st.markdown("---")
        st.markdown("### ➕ My Added Recipes")
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT * FROM recipes WHERE created_by = %s ORDER BY id DESC",
                (user_id,)
            )
            my_recipes = cur.fetchall()

        if not my_recipes:
            st.caption("No recipes added by you yet.")
        for r in my_recipes:
            r = dict(r)
            col1, col2 = st.columns([4, 1])
            col1.write(f"🍽️ {r['name']} — {r['cuisine']} · {r['diet']}")
            with col2:
                if st.button("🗑️ Delete", key=f"del_{r['id']}"):
                    with db.get_cursor() as cur:
                        cur.execute(
                            "DELETE FROM recipes WHERE id=%s AND created_by=%s",
                            (r["id"], user_id)
                        )
                    st.success(f"'{r['name']}' deleted.")
                    st.rerun()

# ── SEED DATABASE ─────────────────────────────────────────────────────────────
elif choice == "Seed Database":
    st.subheader("🌱 Seed Database")
    st.info("""
    Scrapes **50 real recipes** from AllRecipes.com:
    - Real ingredients and steps
    - Cook time and nutrition info
    - Indian, Italian, Chinese, Mexican, Mediterranean, Global

    ⚠️ Takes 1-2 minutes. Run only once.
    """)

    if st.button("🚀 Start Scraping", use_container_width=True):
        progress_bar = st.progress(0)
        status_text  = st.empty()

        def update_progress(current, total, message):
            progress_bar.progress(current / total)
            status_text.text(f"⏳ {message}")

        with st.spinner("Scraping in progress..."):
            scraper = Scraper()
            success, message = scraper.seed_database(progress_callback=update_progress)

        progress_bar.progress(1.0)

        if success:
            status_text.text("✅ Done!")
            st.success(message)
            st.balloons()
        else:
            status_text.text("❌ Failed.")
            st.error(message)