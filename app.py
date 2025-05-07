from flask import Flask, jsonify, request
import pandas as pd
import random
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def extract_city(location):
    parts = location.split(",")
    return parts[-1].strip() if parts else "Unknown"

def extract_area(location):
    parts = location.split(",")
    return parts[0].strip() if parts else "Unknown"

def clean_bhk(bhk):
    if pd.isna(bhk) or str(bhk).strip() in ["N/A", "NA", "-", ""]:
        return ""
    return str(bhk).strip()

def load_data():
    df = pd.read_csv("cleaned_99acres.csv")
    df["city"] = df["Location"].apply(extract_city)
    df["area"] = df["Location"].apply(extract_area)
    df.rename(columns={"Bedrooms": "BHK"}, inplace=True)
    df["BHK"] = df["BHK"].apply(clean_bhk)
    df.fillna("", inplace=True)
    return df

@app.route("/data")
def data():
    df = load_data()
    return jsonify(df.to_dict(orient="records"))

@app.route("/filter")
def filter_data():
    search_term = request.args.get("term", "").lower()
    df = load_data()
    filtered = df[df["city"].str.contains(search_term, case=False, na=False)]
    return jsonify(filtered.to_dict(orient="records"))

@app.route("/cities")
def get_cities():
    df = load_data()
    cities = sorted(df["city"].dropna().unique().tolist())
    return jsonify(cities)

@app.route("/areas")
def get_areas():
    city = request.args.get("city", "")
    df = load_data()
    areas = sorted(df[df["city"].str.lower() == city.lower()]["area"].unique().tolist())
    return jsonify(areas)

@app.route("/average_price")
def average_price():
    city = request.args.get("city", "")
    df = load_data()
    df_city = df[df["city"].str.lower() == city.lower()]
    try:
        df_city["Price"] = df_city["Price"].str.replace(",", "").astype(float)
        avg_price = df_city["Price"].mean()
    except:
        avg_price = None
    return jsonify({"city": city, "average_price": avg_price})

@app.route("/bhk_distribution")
def bhk_distribution():
    city = request.args.get("city", "")
    df = load_data()
    df_city = df[df["city"].str.lower() == city.lower()]
    bhk_counts = df_city["BHK"].value_counts().to_dict()
    return jsonify(bhk_counts)

@app.route("/top_expensive")
def top_expensive():
    N = int(request.args.get("n", 5))
    df = load_data()
    try:
        df["Price"] = df["Price"].str.replace(",", "").astype(float)
    except:
        df["Price"] = 0
    top_props = df.sort_values(by="Price", ascending=False).head(N)
    return jsonify(top_props.to_dict(orient="records"))

@app.route("/price_range")
def price_range():
    min_price = float(request.args.get("min", 0))
    max_price = float(request.args.get("max", 1e9))
    df = load_data()
    try:
        df["Price"] = df["Price"].str.replace(",", "").astype(float)
    except:
        df["Price"] = 0
    filtered = df[(df["Price"] >= min_price) & (df["Price"] <= max_price)]
    return jsonify(filtered.to_dict(orient="records"))

@app.route("/city_leaderboard")
def city_leaderboard():
    df = load_data()
    counts = df["city"].value_counts().to_dict()
    return jsonify(counts)

@app.route("/area_summary")
def area_summary():
    city = request.args.get("city", "")
    df = load_data()
    try:
        df["Price"] = df["Price"].str.replace(",", "").astype(float)
    except:
        df["Price"] = 0
    df_city = df[df["city"].str.lower() == city.lower()]
    summary = df_city.groupby("area")["Price"].agg(["mean", "median", "min", "max"]).fillna(0).to_dict()
    return jsonify(summary)

@app.route("/random_property")
def random_property():
    df = load_data()
    random_row = df.sample(1).to_dict(orient="records")[0]
    return jsonify(random_row)

@app.route("/search_description")
def search_description():
    keyword = request.args.get("q", "").lower()
    df = load_data()
    if "Description" not in df.columns:
        return jsonify({"error": "No Description column in dataset"}), 400
    matches = df[df["Description"].str.lower().str.contains(keyword, na=False)]
    return jsonify(matches.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)
