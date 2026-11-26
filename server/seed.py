"""Load demo data: 2 sellers, 1 empty shopper, 8 reviewers, 3 products, ~22 reviews.

    uv run python seed.py           # refuses if demo data already exists
    uv run python seed.py --reset   # wipes the database first

Every review goes through the real analysis pipeline, so the first run loads
the models (and downloads them if needed).
"""
import shutil
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
from PIL import Image

from app import create_app
from app.db import get_db
from app.service import analyze

ASSETS = Path(__file__).parent / "seed_assets"
PASSWORD = "password123"
NOW = datetime.now(timezone.utc)


def pct(x, y, w=1200, h=800):
    return round(x / w * 100, 2), round(y / h * 100, 2)


def part(name, xy, keywords=()):
    x, y = pct(*xy)
    return {"id": uuid.uuid4().hex[:10], "name": name, "keywords": list(keywords), "x": x, "y": y}


PRODUCTS = [
    {
        "seller": "seller@demo.com",
        "image": "shoe.png",
        "name": "Trailblazer Leather Sneaker",
        "category": "Footwear",
        "price": 4999,
        "description": "Full-grain leather sneaker with a cushioned midsole and a grippy rubber outsole. "
                       "Built for city streets and weekend trails.",
        "aspects": [
            part("Leather", (420, 430), ["upper"]),
            part("Laces", (660, 350), ["strings", "shoelace"]),
            part("Tongue", (620, 210)),
            part("Toe cap", (980, 480), ["toe box", "toe"]),
            part("Heel", (215, 240), ["heel tab", "collar", "ankle"]),
            part("Stitching", (520, 510), ["seams", "stitches"]),
            part("Sole", (620, 600), ["grip", "outsole", "tread", "traction"]),
        ],
        "reviews": [
            "The shoe leather quality is very good but lace quality is not so good.",
            "Love the leather, it has softened nicely after two weeks. The grip on wet pavement is excellent. "
            "The laces keep coming undone though.",
            "The sole wore down unevenly after a month and the stitching near the toe is already coming apart. Disappointed.",
            "Gorgeous shoes. The toe cap scuffs really easily, but the heel is comfortable and doesn't rub.",
            "The tongue keeps sliding to one side, which is annoying. Otherwise the leather and sole are solid.",
            "Traction is fantastic on trails. The laces frayed within a week and I had to replace them.",
            "Stitching is neat and strong. The leather feels premium. The heel collar rubbed my ankle for the first few days.",
            "Toe box is roomy and the toe cap looks great. The sole is a bit stiff at first.",
        ],
    },
    {
        "seller": "seller@demo.com",
        "image": "phone.png",
        "name": "Nova X2 Smartphone",
        "category": "Electronics",
        "price": 29999,
        "description": "6.5\" 120Hz OLED display, triple 50MP camera, 5000mAh battery with 33W fast charging "
                       "and an aluminium frame.",
        "aspects": [
            part("Display", (370, 300), ["screen"]),
            part("Speaker", (370, 711), ["audio", "volume"]),
            part("Build quality", (520, 420), ["frame", "body"]),
            part("Camera", (787, 189), ["photos", "selfie", "lens"]),
            part("Battery", (830, 460), ["charging", "charge"]),
            part("Design", (830, 640), ["looks", "back panel", "finish", "colour"]),
        ],
        "reviews": [
            "Battery life is amazing, easily lasts two days, but the screen is dim outdoors and the photos come out grainy.",
            "The display is gorgeous and super smooth. The camera is excellent in daylight. Battery drains quickly when gaming.",
            "Looks stunning and feels premium. Charging is slow though.",
            "The camera and display are both fantastic. However, it overheats when charging.",
            "The speaker is loud and clear. The frame feels cheap and creaks a bit.",
            "Night photos are blurry and the selfie camera is average. The screen is bright and sharp.",
            "Build quality is excellent, it survived a drop without a scratch. The back panel is a fingerprint magnet.",
            "Battery easily lasts a full day. The speaker sounds tinny at high volume.",
        ],
    },
    {
        "seller": "audio@demo.com",
        "image": "headphones.png",
        "name": "Echo Studio Wireless Headphones",
        "category": "Audio",
        "price": 7499,
        "description": "Over-ear wireless headphones with 40mm drivers, memory-foam ear cushions, a boom "
                       "microphone and 40-hour battery life.",
        "aspects": [
            part("Headband", (600, 110), ["band"]),
            part("Ear cushions", (345, 565), ["ear pads", "pads", "cushion", "earcups"]),
            part("Sound", (865, 565), ["audio", "bass", "treble", "music"]),
            part("Microphone", (1016, 700), ["mic", "calls"]),
            part("Battery", (255, 555), ["charge", "charging"]),
        ],
        "reviews": [
            "The sound is rich with deep bass. The ear cushions get hot after an hour.",
            "The headband is too tight and gives me a headache. The audio quality is superb though.",
            "Ear pads are soft and comfortable. The microphone picks up a lot of background noise on calls.",
            "Battery lasts forever, I charge it once a week. The headband padding started peeling after three months.",
            "Mic is clear and colleagues hear me perfectly. The bass is a bit muddy.",
            "Comfortable cushions, sturdy headband, great sound. Best headphones I have owned.",
        ],
    },
]

SELLERS = [("seller@demo.com", "Stride & Co"), ("audio@demo.com", "Northwind Audio")]
REVIEWERS = ["Aarav Mehta", "Priya Sharma", "Rohan Gupta", "Sneha Iyer",
             "Vikram Singh", "Ananya Rao", "Kabir Khan", "Meera Nair"]


def make_user(db, email, name, role):
    user = {"name": name, "email": email, "role": role, "created_at": NOW - timedelta(days=90),
            "password_hash": bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()}
    user["_id"] = db.users.insert_one(user).inserted_id
    return user


def main():
    app = create_app({"WARM_MODELS": False})
    with app.app_context():
        db = get_db()
        if "--reset" in sys.argv:
            app.extensions["mongo_client"].drop_database(app.config["MONGO_DB"])
            for f in app.config["UPLOAD_DIR"].glob("*"):
                f.unlink()
            from app.db import init_db
            init_db(app)
            db = get_db()
        elif db.users.find_one({"email": "seller@demo.com"}):
            print("Demo data already exists. Run with --reset to wipe and reload it.")
            return

        sellers = {email: make_user(db, email, name, "provider") for email, name in SELLERS}
        make_user(db, "shopper@demo.com", "Demo Shopper", "consumer")
        reviewers = [make_user(db, f"{n.split()[0].lower()}@demo.com", n, "consumer") for n in REVIEWERS]

        upload_dir = app.config["UPLOAD_DIR"]
        upload_dir.mkdir(parents=True, exist_ok=True)
        print("Analysing demo reviews (loads the models on first run)...")
        for p_index, spec in enumerate(PRODUCTS):
            filename = f"{uuid.uuid4().hex}.png"
            shutil.copy(ASSETS / spec["image"], upload_dir / filename)
            with Image.open(upload_dir / filename) as img:
                width, height = img.size
            seller = sellers[spec["seller"]]
            created = NOW - timedelta(days=60 - p_index * 5)
            product = {
                "name": spec["name"], "description": spec["description"], "category": spec["category"],
                "price": spec["price"], "image": filename, "image_width": width, "image_height": height,
                "aspects": spec["aspects"], "provider_id": seller["_id"], "provider_name": seller["name"],
                "created_at": created, "updated_at": created,
            }
            product["_id"] = db.products.insert_one(product).inserted_id

            for r_index, text in enumerate(spec["reviews"]):
                author = reviewers[(r_index + p_index * 3) % len(reviewers)]
                when = NOW - timedelta(days=50 - r_index * 6 - p_index, hours=r_index * 3)
                result = analyze(text, product["aspects"])
                db.reviews.insert_one({
                    "product_id": product["_id"], "user_id": author["_id"], "user_name": author["name"],
                    "text": text, **result, "created_at": when, "updated_at": when, "analyzed_at": NOW,
                })
                tags = ", ".join(f"{m['aspect_name']}:{m['label'][:3]}" for m in result["mentions"]) or "(general)"
                print(f"  {spec['name'][:22]:<22} | {tags}")

        print("\nDemo data loaded. Log in with password 'password123' as:")
        print("  seller@demo.com   - seller (Trailblazer Sneaker, Nova X2)")
        print("  audio@demo.com    - seller (Echo Studio Headphones)")
        print("  shopper@demo.com  - shopper with no reviews yet")
        print("  aarav@demo.com, priya@demo.com, ... - shoppers who already reviewed")


if __name__ == "__main__":
    main()
