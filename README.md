# AspectLens: Aspect-Based Product Review Sentiment

Normal e-commerce reviews are a single blob of text. AspectLens lets shoppers write one ordinary review,
then **splits it into the product parts it talks about, scores each part, and pins the result onto the
product photo**.

> *"The shoe leather quality is very good but lace quality is not so good"*
> → **Leather** ★4.3 positive · **Laces** ★2.3 negative

Each marked part of the product shows a coloured dot (green / amber / red / grey = no reviews yet).
Hovering over a dot opens a panel with that part's average stars, a positive/neutral/negative split, and every
review snippet about that part.

## Two kinds of account

| Shopper | Seller |
|---|---|
| Browse and search products | List products (photo, details, price) |
| Hover over the dots to read reviews part by part | Click on the photo to drop a dot on each part and name it |
| Write, preview, edit or delete one review per product | Add synonyms per part ("grip, tread" for *Sole*) |
| | Test a sample review against their parts |

Because the sellers define the parts, the system works for **any** product, not just the demo ones.
Changing a product's parts re-analyses all of its existing reviews.

## How the analysis works (`server/app/nlp/`)

1. **Split** the review into sentences → contrast segments (*but, however, although…*) → fragments (*and*, commas).
2. **Match** fragments to the seller's parts:
   - *keywords*: the part name or a seller synonym, with plurals and compound words ("shoelaces" → *Lace*);
   - *semantic*: `all-MiniLM-L6-v2` embeddings catch synonyms nobody typed ("traction" → *Sole*, "photos" → *Camera*).
3. **Assemble clauses**:
   - "The camera **and** display are fantastic" rates both parts.
   - "sturdy, durable **and** comfortable" stays with the sole.
   - "**They** snapped after a week" goes to the part mentioned just before.
4. **Score** each clause with `nlptown/bert-base-multilingual-uncased-sentiment`, using the *expected* star value
   (1.0–5.0) rather than the top label. ≥ 3.3 counts as positive and ≤ 2.7 as negative; these cut-offs were
   tuned on a hand-labelled set.

## Run it

Prerequisites (already installed on this machine under `~/.local`): Node 22+, MongoDB 8, and [uv](https://docs.astral.sh/uv/) (Python 3.12).

```bash
./scripts/dev.sh                          # MongoDB + API (:5050) + web app (:5173)
cd server && uv run python seed.py --reset   # optional: demo products and reviews
```

Open **http://localhost:5173**. Every demo account uses the password `password123`:

| Account | Role |
|---|---|
| `shopper@demo.com` | shopper with no reviews yet (try writing one) |
| `seller@demo.com` | seller of the sneaker and the phone |
| `audio@demo.com` | seller of the headphones |

The first run downloads about 800 MB of models. Set `NLP_MODE=lite` in `server/.env` for a no-download,
keyword-only mode (useful on low-RAM machines).

## Tests

```bash
cd server
uv run pytest -m "not slow"   # 28 fast tests: splitting rules + full API (needs MongoDB running)
uv run pytest                 # + 8 tests against the real models
```

## Layout

```
server/            Flask API (Python 3.12, uv)
  app/auth.py      register/login, JWT, consumer/provider roles
  app/products.py  products, image upload, part (aspect) editing
  app/reviews.py   reviews, preview, edit/delete
  app/service.py   analysis + per-part aggregation
  app/nlp/         splitting, matching, sentiment
  seed.py          demo data;  seed_assets/  demo illustrations
client/            React 19 + Vite + React Router
  src/pages/       Catalog, ProductPage, Login/Register, seller Dashboard, ProductForm, PartEditor
  src/components/  HotspotViewer, AspectPanel, ReviewComposer, ReviewList…
scripts/           dev.sh, start-mongo.sh, stop-mongo.sh
```

## Known limitations

- Sentiment comes from a general review model, so slang can be misread ("the bass is *punchy*" scores slightly
  negative) and sarcasm is not detected.
- Semantic matching needs a similarity of at least 0.5. Near-misses such as "grip" → *Sole* need a seller keyword.
- Reviews are analysed synchronously. Re-analysing after a part change is fine for hundreds of reviews, but a
  background job queue would be needed for very large catalogues.
