from conftest import png_bytes


# ------------------------------------------------------------------- auth
def test_register_login_me(client, register):
    headers, user = register("consumer", email="ana@example.com", name="Ana")
    assert user["role"] == "consumer"
    res = client.post("/api/auth/login", json={"email": "ANA@example.com", "password": "password123"})
    assert res.status_code == 200
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {res.get_json()['token']}"})
    assert me.get_json()["user"]["email"] == "ana@example.com"
    assert "password_hash" not in me.get_json()["user"]


def test_register_validation_and_duplicates(client, register):
    res = client.post("/api/auth/register", json={"name": "", "email": "bad", "password": "x", "role": "admin"})
    assert res.status_code == 422
    assert set(res.get_json()["fields"]) == {"name", "email", "password", "role"}
    register(email="dup@example.com")
    res = client.post("/api/auth/register", json={"name": "B", "email": "dup@example.com",
                                                   "password": "password123", "role": "consumer"})
    assert res.status_code == 409


def test_wrong_password_and_bad_token(client, register):
    register(email="c@example.com")
    assert client.post("/api/auth/login", json={"email": "c@example.com", "password": "nope12345"}).status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    assert client.get("/api/auth/me").status_code == 401


# --------------------------------------------------------------- products
def test_only_providers_create_products(client, register):
    headers, _ = register("consumer")
    res = client.post("/api/products", headers=headers, content_type="multipart/form-data",
                      data={"name": "X", "image": (png_bytes(), "x.png")})
    assert res.status_code == 403


def test_create_product_validates_image(client, register):
    headers, _ = register("provider")
    res = client.post("/api/products", headers=headers, content_type="multipart/form-data",
                      data={"name": "X", "image": (__import__("io").BytesIO(b"not an image"), "x.png")})
    assert res.status_code == 422 and "image" in res.get_json()["fields"]


def test_product_lifecycle(client, shoe):
    product, headers = shoe
    assert product["image_width"] == 400 and product["price"] == 89.99
    assert [a["name"] for a in product["aspects"]] == ["Leather", "Lace", "Sole"]
    assert client.get(product["image_url"]).status_code == 200

    listing = client.get("/api/products").get_json()["products"]
    assert listing[0]["id"] == product["id"] and listing[0]["aspect_count"] == 3
    assert client.get("/api/products?q=trail").get_json()["products"]
    assert not client.get("/api/products?q=nothing-like-this").get_json()["products"]
    assert len(client.get("/api/products?mine=1", headers=headers).get_json()["products"]) == 1
    assert client.get("/api/categories").get_json()["categories"] == [{"name": "Footwear", "count": 1}]
    assert len(client.get("/api/products?category=footwear").get_json()["products"]) == 1
    assert not client.get("/api/products?category=Foot").get_json()["products"]

    res = client.patch(f"/api/products/{product['id']}", headers=headers,
                       content_type="multipart/form-data", data={"name": "Trail Runner 2"})
    assert res.get_json()["product"]["name"] == "Trail Runner 2"

    assert client.delete(f"/api/products/{product['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/products/{product['id']}").status_code == 404


def test_other_provider_cannot_edit(client, shoe, register):
    product, _ = shoe
    other, _ = register("provider")
    assert client.put(f"/api/products/{product['id']}/aspects", headers=other,
                      json={"aspects": []}).status_code == 403
    assert client.delete(f"/api/products/{product['id']}", headers=other).status_code == 403


def test_aspect_validation(client, shoe):
    product, headers = shoe
    url = f"/api/products/{product['id']}/aspects"
    assert client.put(url, headers=headers, json={"aspects": [{"name": "A", "x": 150, "y": 5}]}).status_code == 422
    dup = [{"name": "Lace", "x": 1, "y": 1}, {"name": "lace", "x": 2, "y": 2}]
    assert client.put(url, headers=headers, json={"aspects": dup}).status_code == 422
    assert client.put(url, headers=headers, json={"aspects": [{"name": "", "x": 1, "y": 1}]}).status_code == 422


def test_bad_ids_are_404(client):
    assert client.get("/api/products/not-an-id").status_code == 404
    assert client.get("/api/products/000000000000000000000000").status_code == 404


# ---------------------------------------------------------------- reviews
def test_review_is_split_into_parts_and_aggregated(client, shoe, register):
    product, _ = shoe
    ana, _ = register("consumer", name="Ana")
    ben, _ = register("consumer", name="Ben")

    res = client.post(f"/api/products/{product['id']}/reviews", headers=ana,
                      json={"text": "The leather quality is very good but lace quality is not so good"})
    assert res.status_code == 201
    mentions = {m["aspect_name"]: m for m in res.get_json()["review"]["mentions"]}
    assert mentions["Leather"]["label"] == "positive"
    assert mentions["Lace"]["label"] == "negative"

    client.post(f"/api/products/{product['id']}/reviews", headers=ben,
                json={"text": "Lovely leather. The strings broke after a week."})

    detail = client.get(f"/api/products/{product['id']}", headers=ana).get_json()["product"]
    parts = {a["name"]: a for a in detail["aspects"]}
    assert parts["Leather"]["summary"]["count"] == 2
    assert parts["Leather"]["summary"]["positive"] == 2
    assert parts["Lace"]["summary"]["negative"] == 2  # "strings" is a seller keyword
    assert {s["user_name"] for s in parts["Lace"]["snippets"]} == {"Ana", "Ben"}
    assert parts["Sole"]["summary"]["count"] == 0 and parts["Sole"]["summary"]["avg_stars"] is None
    assert detail["overall"]["count"] == 2
    assert detail["viewer"]["can_review"] and detail["viewer"]["my_review_id"]

    listing = client.get("/api/products").get_json()["products"][0]
    assert listing["overall"]["count"] == 2


def test_one_review_per_consumer_and_edit_delete(client, shoe, register):
    product, _ = shoe
    ana, _ = register("consumer")
    url = f"/api/products/{product['id']}/reviews"
    rid = client.post(url, headers=ana, json={"text": "The sole is excellent"}).get_json()["review"]["id"]
    assert client.post(url, headers=ana, json={"text": "The sole is excellent again"}).status_code == 409

    res = client.put(f"/api/reviews/{rid}", headers=ana, json={"text": "The sole is terrible now"})
    assert res.get_json()["review"]["mentions"][0]["label"] == "negative"

    other, _ = register("consumer")
    assert client.delete(f"/api/reviews/{rid}", headers=other).status_code == 403
    assert client.delete(f"/api/reviews/{rid}", headers=ana).status_code == 200
    assert client.get(url).get_json()["reviews"] == []


def test_providers_cannot_review_and_text_is_validated(client, shoe, register):
    product, provider = shoe
    url = f"/api/products/{product['id']}/reviews"
    assert client.post(url, headers=provider, json={"text": "My own product is great"}).status_code == 403
    ana, _ = register("consumer")
    assert client.post(url, headers=ana, json={"text": "short"}).status_code == 422


def test_changing_parts_reanalyzes_existing_reviews(client, shoe, register):
    product, provider = shoe
    ana, _ = register("consumer")
    client.post(f"/api/products/{product['id']}/reviews", headers=ana,
                json={"text": "The heel tab is flimsy and the leather is great"})
    detail = client.get(f"/api/products/{product['id']}").get_json()["product"]
    assert "Heel tab" not in {a["name"] for a in detail["aspects"]}

    aspects = [{k: a[k] for k in ("id", "name", "keywords", "x", "y")} for a in detail["aspects"]]
    aspects.append({"name": "Heel tab", "x": 10, "y": 50})
    res = client.put(f"/api/products/{product['id']}/aspects", headers=provider, json={"aspects": aspects})
    assert res.get_json()["reanalyzed_reviews"] == 1
    parts = {a["name"]: a for a in res.get_json()["product"]["aspects"]}
    assert parts["Heel tab"]["summary"]["negative"] == 1
    assert parts["Leather"]["id"] == detail["aspects"][0]["id"]  # ids are stable


def test_preview_does_not_save(client, shoe, register):
    product, _ = shoe
    ana, _ = register("consumer")
    res = client.post(f"/api/products/{product['id']}/analyze", headers=ana,
                      json={"text": "The laces are terrible"})
    assert res.get_json()["analysis"]["mentions"][0]["aspect_name"] == "Lace"
    assert client.get(f"/api/products/{product['id']}/reviews").get_json()["reviews"] == []


def test_health(client):
    body = client.get("/api/health").get_json()
    assert body["database"] == "ok"
