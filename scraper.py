from __future__ import annotations

import requests
import time
from db import db

BASE_URL = "https://www.themealdb.com/api/json/v1/1"

AREA_TO_CUISINE = {
    "Indian":        "Indian",
    "Italian":       "Italian",
    "Chinese":       "Chinese",
    "Mexican":       "Mexican",
    "Greek":         "Mediterranean",
    "Spanish":       "Mediterranean",
    "Moroccan":      "Mediterranean",
    "Turkish":       "Mediterranean",
    "American":      "Global",
    "British":       "Global",
    "French":        "Global",
    "Japanese":      "Global",
    "Thai":          "Global",
    "Jamaican":      "Global",
    "Unknown":       "Global",
}

CATEGORY_TO_DIET = {
    "Vegetarian":    "Veg",
    "Vegan":         "Vegan",
    "Seafood":       "Non-Veg",
    "Chicken":       "Non-Veg",
    "Beef":          "Non-Veg",
    "Lamb":          "Non-Veg",
    "Pork":          "Non-Veg",
    "Pasta":         "Veg",
    "Dessert":       "Veg",
    "Breakfast":     "Veg",
    "Side":          "Veg",
    "Starter":       "Veg",
    "Miscellaneous": "Veg",
    "Goat":          "Non-Veg",
}

NUTRITION_DEFAULTS = {
    "Non-Veg": {"calories": 420, "protein": 30, "carbs": 25, "fat": 18},
    "Veg":     {"calories": 320, "protein": 12, "carbs": 40, "fat": 10},
    "Vegan":   {"calories": 280, "protein": 10, "carbs": 42, "fat": 8},
}


class Scraper:

    def _get(self, url):
        res = requests.get(url, timeout=10)
        return res.json()

    def _get_all_categories(self):
        print("📋 Fetching categories from TheMealDB...")
        data       = self._get(f"{BASE_URL}/categories.php")
        categories = data.get("categories", [])
        names      = [c["strCategory"] for c in categories]
        print(f"   ✅ Found {len(names)} categories: {', '.join(names)}")
        return names

    def _get_meals_by_category(self, category):
        data  = self._get(f"{BASE_URL}/filter.php?c={category}")
        meals = data.get("meals") or []
        return meals

    def _get_full_meal(self, meal_id):
        data  = self._get(f"{BASE_URL}/lookup.php?i={meal_id}")
        meals = data.get("meals") or []
        return meals[0] if meals else None

    def _parse_meal(self, meal):
        try:
            name = meal.get("strMeal", "").strip()
            if not name:
                return None

            area     = meal.get("strArea", "Unknown")
            cuisine  = AREA_TO_CUISINE.get(area, "Global")

            category = meal.get("strCategory", "Miscellaneous")
            diet     = CATEGORY_TO_DIET.get(category, "Veg")

            time_map = {
                "Dessert": 30, "Breakfast": 15,
                "Seafood": 20, "Pasta": 25, "Side": 20,
            }
            cooking_time = time_map.get(category, 35)

            ingredients = []
            for i in range(1, 21):
                ing     = (meal.get(f"strIngredient{i}") or "").strip()
                measure = (meal.get(f"strMeasure{i}") or "").strip()
                if ing:
                    full = f"{measure} {ing}".strip() if measure else ing
                    ingredients.append(full)

            if not ingredients:
                return None

            raw   = (meal.get("strInstructions") or "").strip()
            steps = [
                s.strip() for s in raw.split("\n")
                if s.strip() and len(s.strip()) > 10
            ]
            if not steps:
                steps = [
                    s.strip() for s in raw.split("\r\n")
                    if s.strip() and len(s.strip()) > 10
                ]
            if not steps:
                steps = [raw[:500]]

            if not steps:
                return None

            defaults = NUTRITION_DEFAULTS.get(diet, NUTRITION_DEFAULTS["Veg"])

            return {
                "name":         name,
                "cuisine":      cuisine,
                "diet":         diet,
                "cooking_time": cooking_time,
                "calories":     defaults["calories"],
                "protein":      defaults["protein"],
                "carbs":        defaults["carbs"],
                "fat":          defaults["fat"],
                "ingredients":  ingredients,
                "steps":        steps,
            }

        except Exception as e:
            print(f"   ❌ Parse error: {e}")
            return None

    def _already_exists(self, name):
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT id FROM recipes WHERE name = %s", (name,)
            )
            return cur.fetchone() is not None

    def _insert_recipe(self, recipe):
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """INSERT INTO recipes
                       (name, cuisine, diet, cooking_time, calories, protein, carbs, fat)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (
                        recipe["name"],     recipe["cuisine"],
                        recipe["diet"],     recipe["cooking_time"],
                        recipe["calories"], recipe["protein"],
                        recipe["carbs"],    recipe["fat"]
                    )
                )
                recipe_id = cur.fetchone()["id"]

                for ing in recipe["ingredients"]:
                    cur.execute(
                        "INSERT INTO ingredients (recipe_id, ingredient) VALUES (%s, %s)",
                        (recipe_id, ing)
                    )
                for step in recipe["steps"]:
                    cur.execute(
                        "INSERT INTO steps (recipe_id, step) VALUES (%s, %s)",
                        (recipe_id, step)
                    )
            return True
        except Exception as e:
            print(f"   ❌ DB error: {e}")
            return False

    def seed_database(self, target=50, progress_callback=None):
        inserted = 0
        seen_ids = set()

        categories = self._get_all_categories()

        print(f"\n🍳 Starting scrape — target: {target} recipes\n")

        for category in categories:
            if inserted >= target:
                break

            print(f"\n📂 Category: {category}")
            meals = self._get_meals_by_category(category)
            print(f"   Found {len(meals)} meals")

            for meal_summary in meals:
                if inserted >= target:
                    break

                meal_id   = meal_summary.get("idMeal")
                meal_name = meal_summary.get("strMeal", "")

                if meal_id in seen_ids:
                    continue
                seen_ids.add(meal_id)

                if self._already_exists(meal_name):
                    print(f"   ⏭️  Already exists: {meal_name}")
                    continue

                full_meal = self._get_full_meal(meal_id)
                if not full_meal:
                    continue

                recipe = self._parse_meal(full_meal)
                if not recipe:
                    print(f"   ⚠️  Could not parse: {meal_name}")
                    continue

                if self._insert_recipe(recipe):
                    inserted += 1
                    msg = (
                        f"[{inserted}/{target}] {recipe['name']} | "
                        f"{recipe['cuisine']} | {recipe['diet']} | "
                        f"{len(recipe['ingredients'])} ingredients | "
                        f"{len(recipe['steps'])} steps"
                    )
                    print(f"   ✅ {msg}")

                    if progress_callback:
                        progress_callback(inserted, target, f"[{inserted}/{target}] {recipe['name']}")

                time.sleep(0.3)

        if inserted == 0:
            return False, "No recipes inserted. Check internet connection."

        return True, f"✅ Done! Scraped and inserted {inserted} real recipes from TheMealDB!"


def scrape_recipes():
    scraper = Scraper()
    success, message = scraper.seed_database(target=50)
    print(f"\n{message}")


if __name__ == "__main__":
    scrape_recipes()










