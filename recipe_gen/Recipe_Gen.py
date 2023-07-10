import pandas as pd
from recipe_scrapers import scrape_me
from recipe_scrapers._exceptions import WebsiteNotImplementedError
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("prepr_fb_secret.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


def parse_recipe_json_to_df():
    """
    Parse recipe json file to dataframe
    """
    # Read in recipe json file
    recipe_json = pd.read_json("recipes.json", lines=True)

    # Create dataframe from recipe json
    recipe_df = pd.DataFrame(recipe_json)

    # Return dataframe
    return recipe_df


def scrape_recipes_df_urls(recipe_df):
    """
    Scrape urls from recipe dataframe
    """
    # Create list of urls
    recipe_urls = recipe_df["url"].tolist()

    for url in recipe_urls[:19000]:
        try:
            scraper = scrape_me(url)

            print(scraper.title())
            recipe = {
                "title": scraper.title(),
                "yields": scraper.yields(),
                "ingredients": scraper.ingredients(),
                "instructions": scraper.instructions(),
                "image": scraper.image(),
                "host": scraper.host(),
                "links": scraper.links(),
                "nutrients": scraper.nutrients(),
            }
            db.collection("recipe_generator_store").add(recipe)
        except Exception:
            print(url + "failed")
            pass


if __name__ == "__main__":
    df = parse_recipe_json_to_df()
    scrape_recipes_df_urls(df)
    print(df.columns)
