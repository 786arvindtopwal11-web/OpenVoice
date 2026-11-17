# 🤖 YouTube Comment Reply Bot: Setup Guide (Step by Step)

## Ye bot kaise kaam karta hai

```
Har 3 ghante ──► Bot naye YouTube comments padhta hai
                      │
                      ▼
               Claude AI har comment ka draft reply likhta hai
                      │
                      ▼
               Har comment ke liye GitHub par ek "Issue" banta hai
                      │
                      ▼
   Aap phone par GitHub app kholte hain aur draft padhte hain
        │                 │                     │
   approve label     Edit karke approve     reject label
        │                 │                     │
        ▼                 ▼                     ▼
   Reply YouTube par post ho jata hai      Kuch post nahi hota
```

Aapki marzi ke bina **koi bhi reply post nahi hota**.

Setup mein kul **7 steps** hain, lagbhag 30–40 minute lagenge. Computer par
karna aasaan rahega. Baad mein roz ka kaam phone se ho jayega.

---

## Step 1: Code ko `main` branch mein laaiye

Bot ka code `ccr-db2cd493-003wkc` branch par hai. GitHub ke scheduled
workflows sirf **main** branch se chalte hain, isliye ise merge karna zaroori hai.

1. Apne repo par jaiye: `github.com/786arvindtopwal11-web/OpenVoice`
2. Upar peela banner dikhega: **"ccr-db2cd493-003wkc had recent pushes"**.
   Wahan **Compare & pull request** dabaiye.
   (Banner na dikhe to **Pull requests → New pull request** mein jaiye,
   `base: main` aur `compare: ccr-db2cd493-003wkc` chuniye.)
3. **Create pull request** dabaiye, phir **Merge pull request → Confirm merge**.

---

## Step 2: Repo mein Issues aur Actions chalu kariye

Forked repo mein ye dono kabhi-kabhi band rehte hain.

1. Repo mein **Settings → General** kholiye.
2. Neeche **Features** section mein **Issues** ka ✅ tick lagaiye.
3. Ab upar **Actions** tab par jaiye. Agar
   *"Workflows aren't being run on this forked repository"* likha aaye, to
   **I understand my workflows, go ahead and enable them** dabaiye.

> ⚠️ **Dhyan dein:** Agar repo **public** hai, to Issues (comments aur draft
> replies) sabko dikhenge. YouTube comments waise bhi public hote hain, lekin
> chahein to is bot ke liye ek nayi **private** repo bana kar ye files
> (`youtube-comment-bot/` folder aur `.github/workflows/` ki do `yt-*.yml` files)
> wahan copy kar sakte hain. Private repo mein har mahine 2000 minute free milte hain,
> jo is bot ke liye kaafi hain.

---

## Step 3: Google Cloud mein YouTube API chalu kariye

1. **https://console.cloud.google.com** kholiye aur usi Google account se login
   kariye jisse aapka YouTube channel chalta hai.
2. Upar project dropdown → **New Project** → naam: `yt-comment-bot` → **Create**.
   Phir upar se ye naya project select kariye.
3. Search bar mein **YouTube Data API v3** likhiye, use kholiye aur **Enable** dabaiye.

### 3A: OAuth consent screen (app ki pehchaan)

4. Left menu mein **APIs & Services → OAuth consent screen** kholiye.
   (Naye design mein iska naam **Google Auth Platform** hai.)
5. **Get started** ya **Configure** dabaiye aur ye bhariye:
   - App name: `YT Comment Bot`
   - User support email: apna email
   - Audience / User type: **External**
   - Contact email: apna email
   - **Create / Save** dabaiye.
6. 🔴 **Bahut zaroori:** **Audience** (ya *Publishing status*) section mein jaiye aur
   **Publish app** dabaiye, taaki status **In production** ho jaye.
   - Agar ise "Testing" mein chhod diya, to har **7 din** mein token expire
     ho jayega aur bot band ho jayega.
   - Google review ki zaroorat nahi hai, kyunki ye app sirf aap khud use kar rahe hain.

### 3B: Client ID aur Secret banaiye

7. **Credentials → + Create credentials → OAuth client ID** kholiye
   (ya **Clients → Create client**).
8. Application type: **Web application**, Name: `bot`.
9. **Authorized redirect URIs** mein **+ Add URI** dabaiye aur ye bilkul aise hi paste kariye:
   ```
   https://developers.google.com/oauthplayground
   ```
10. **Create** dabaiye. Ab **Client ID** aur **Client Secret** dikhenge. Dono ko
    Notepad mein copy kar lijiye.

---

## Step 4: Refresh Token nikaliye (ek baar ka kaam)

Isi token se bot aapke channel ki taraf se reply kar payega.

1. **https://developers.google.com/oauthplayground** kholiye.
2. Upar daayein ⚙️ (gear icon) dabaiye:
   - ✅ **Use your own OAuth credentials** tick kariye
   - Client ID aur Client Secret (Step 3 wale) paste kariye
   - Popup band kar dijiye
3. Left side **Step 1** mein, neeche wale box (*Input your own scopes*) mein ye paste kariye:
   ```
   https://www.googleapis.com/auth/youtube.force-ssl
   ```
   Phir **Authorize APIs** dabaiye.
4. Apna Google account chuniye. Agar kai channel hain, to **wahi channel chuniye**
   jiske comments ka reply karna hai.
5. *"Google hasn't verified this app"* aaye to **Advanced → Go to YT Comment Bot (unsafe)**
   dabaiye. Ye aapka hi app hai, isliye safe hai. Phir **Continue / Allow** dabaiye.
6. **Step 2** mein **Exchange authorization code for tokens** dabaiye.
7. **Refresh token** wali value (`1//...` se shuru hoti hai) copy karke Notepad mein rakhiye.

> 🔒 Client Secret aur Refresh Token kisi ko mat dikhaiye. Inse aapke channel
> par comment kiya ja sakta hai.

---

## Step 5: Claude (Anthropic) API key banaiye

1. **https://console.anthropic.com** par account banaiye ya login kariye.
2. **Billing / Plans & Billing** mein thode credits daaliye (shuru ke liye $5 kaafi hain).
   Ek comment ka draft lagbhag **$0.01–0.02** (yaani ₹1–2) ka padta hai.
3. **API Keys → Create Key** dabaiye, naam `yt-bot` rakhiye aur key copy kar lijiye
   (`sk-ant-...`). Ye key sirf ek baar dikhti hai.

---

## Step 6: GitHub mein Secrets daaliye

1. Repo mein **Settings → Secrets and variables → Actions** kholiye.
2. **New repository secret** dabaiye aur ye 4 secrets ek-ek karke banaiye
   (naam bilkul aise hi likhne hain, capital letters mein):

| Name | Value |
|---|---|
| `YT_CLIENT_ID` | Step 3 ka Client ID |
| `YT_CLIENT_SECRET` | Step 3 ka Client Secret |
| `YT_REFRESH_TOKEN` | Step 4 ka Refresh token |
| `ANTHROPIC_API_KEY` | Step 5 ki Claude key |

---

## Step 7: Pehli baar chalaiye ▶️

1. Repo mein **Actions** tab kholiye.
2. Left side mein **"YouTube: naye comments laao"** chuniye.
3. Daayein taraf **Run workflow → Run workflow** dabaiye.
4. 1–2 minute baad ✅ (hara tick) aana chahiye.
5. Ab **Issues** tab kholiye. Har naye comment ka ek Issue dikhega jismein draft reply hoga. 🎉

Iske baad bot **har 3 ghante** mein apne aap chalega.

---

## 📱 Roz ka istemaal (phone se)

1. Play Store se **GitHub** app install karke login kariye.
2. Repo kholiye → **Issues**.
3. Ek issue kholiye. Usmein comment aur Claude ka draft reply hoga.
   - ✅ **Reply pasand hai:** Labels → **`approve`**. 1 minute mein reply YouTube par
     chala jayega aur issue apne aap band ho jayega.
   - ✏️ **Thoda badalna hai:** issue ke **⋯ → Edit** mein jaiye. Sirf ```` ``` ````
     ke andar ka reply text badaliye (baaki lines ko mat chhediye), save kariye,
     phir **`approve`** label lagaiye.
   - ❌ **Reply nahi dena:** **`reject`** label lagaiye.
4. 🚫 se shuru hone wale issues woh hain jinhe bot ne skip karne ki salah di
   (jaise spam ya gaali). Ye apne aap band ho jaate hain. Phir bhi reply dena ho, to
   issue **Reopen** kariye, Edit karke reply likhiye aur `approve` lagaiye.

> Sirf **aap (repo owner)** ke lagaye label par hi reply post hota hai.

---

## ⚙️ Apne hisaab se badlaav

| Kya badalna hai | Kahan |
|---|---|
| Reply ka tone ya style | `youtube-comment-bot/channel_style.md` |
| Kisi video ki poori script ya facts dena | `youtube-comment-bot/video_notes/<VIDEO_ID>.md` |
| Kitni der mein chale (abhi har 3 ghante) | `.github/workflows/yt-fetch-comments.yml` mein `cron` |
| Ek baar mein kitne draft (abhi 15) | Usi file mein `MAX_DRAFTS_PER_RUN` |
| Kitne din purane comments tak dekhe (abhi 3) | Usi file mein `LOOKBACK_DAYS` |

---

## 🛠️ Dikkat aaye to

| Error / dikkat | Hal |
|---|---|
| `invalid_grant` | Refresh token expire ho gaya. Check kariye ki Step 3A mein app **In production** hai, phir Step 4 dobara karke naya token `YT_REFRESH_TOKEN` mein daaliye. |
| `insufficientPermissions` / `forbidden` | Token galat channel ya galat scope se bana hai. Step 4 dobara kariye aur sahi channel chuniye. |
| `quotaExceeded` | Aaj ki YouTube limit poori ho gayi (kareeb 200 replies/din). Kal apne aap theek ho jayega. |
| `credit balance is too low` | Anthropic console mein credits daaliye. |
| `approve` lagane par kuch nahi hua | Check kariye ki code **main** mein merge hua hai (Step 1) aur label aapne khud lagaya hai. Actions tab mein error dekhiye. |
| Bot 60 din baad apne aap band ho gaya | GitHub inactive repo ke scheduled workflows band kar deta hai. Actions tab mein jaakar workflow dobara **Enable** kar dijiye. |
