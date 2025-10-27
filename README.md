# ⚽ DRM Live Auto Match Data Updater

This repository automatically scrapes the **latest live match data** 
and updates it every **8 minutes** — completely automated using **GitHub Actions + PHP** 🕒⚙️  

---

## 🚀 Features

✅ Fully automated — runs every 8 minutes  
✅ No manual PHP hosting required  
✅ Uses caching for faster performance (1-hour cache)  
✅ Saves output as `api.json` (ready for API or frontend use)  
✅ Can also be triggered manually anytime  

---

## 🧠 How It Works

1. GitHub Action runs every **8 minutes**.  
2. Generates clean JSON data with structure like:

   ```json
   [
     {
       "id": "abcd1234",
       "match": "Team A vs Team B"
     },
     {
       "id": "efgh5678",
       "match": "Team C vs Team D"
     }
   ]
