# AAHAR AI: Live Nutrition Lookup

## What this adds
- Keeps `data/processed/ifct_foods_clean.csv` as the primary local reference.
- Searches USDA FoodData Central for additional records.
- Lets you add external results to meals and includes their nutrient snapshots in totals.
- Includes each item's source in the meal-plan CSV.
- Keeps recommendations based on IFCT only.

## 1. Install dependencies
Run from the project root:

```powershell
python -m pip install -r requirements.txt
```

## 2. Get a free USDA API key
Request a key at https://api.data.gov/signup/ and see the official guide at https://fdc.nal.usda.gov/api-guide/.

## 3. Store the key
Create `.streamlit` in the project root, then create `.streamlit/secrets.toml`:

```toml
USDA_FDC_API_KEY = "paste_your_key_here"
```

Never commit `secrets.toml` to GitHub. Add these entries to `.gitignore`:

```gitignore
.streamlit/secrets.toml
.env
```

Alternatively, in the current PowerShell terminal:

```powershell
$env:USDA_FDC_API_KEY="paste_your_key_here"
```

## 4. Place the files
- Replace the project-root `app.py` with the supplied `app.py`.
- Add `src/live_nutrition.py` to your existing `src` folder.
- Add `tests/test_live_nutrition.py` to your existing `tests` folder.
- Merge `requirements.txt` dependencies into your existing file if it contains additional packages.

## 5. Test
```powershell
python -m pytest tests/test_live_nutrition.py -v
python -m pytest tests/test_recommend.py tests/test_meal_planner.py -v
```

## 6. Run
```powershell
python -m streamlit run app.py
```

## Important notes
- USDA API access is free with an API key, subject to rate limits.
- Coverage of Indian dishes varies. Use IFCT when a suitable external record is unavailable.
- External results are not written into or merged with the IFCT CSV.
- Missing nutrients remain unknown, not zero.
- USDA nutrient data can vary by data type and preparation. Check the record's source and basis before using it for dietary decisions.
