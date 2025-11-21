# 3. RECEIPT SCANNING & PARSING REQUIREMENTS  
_(Budget, model selection, and GPU feasibility)_

---

## 3.1 Refined User Workflow (Budget-aware)

This stays close to what you already wrote, just making explicit where costs are incurred:

1. **Upload**
   - User drops a receipt (JPG/PNG/WebP/PDF) into the new `ReceiptScanner` component.
   - Frontend enforces size/type limits **before** hitting the API.

2. **Parse via AI**
   - Frontend sends the file to `/api/parse-receipt`.
   - Backend:
     - Stores a **temp copy** (for retries/logging).
     - Calls the configured **ReceiptEngine** (OpenAI / Claude / Gemini / Cloud OCR / local).
     - Gets back structured JSON (items, totals, date, merchant, etc.) + optional confidence scores.

3. **Review / Edit**
   - Frontend displays a form with:
     - Merchant, date, total, tax, payment method
     - Item table (qty / description / unit price / line total)
   - User edits where needed.

4. **Categorize**
   - `CategoryPicker` is embedded or opened side-by-side.
   - User chooses category (and optionally splits into multiple expenses if you support splitting later).

5. **Save Expense**
   - Backend:
     - Moves file from temp to `/uploads/receipts/YYYY/MM/receipt_[timestamp]_[original].ext`.
     - Creates `Expense` row with `receipt_url` set.
     - Optionally logs `ReceiptMetadata` (model used, confidence scores).

6. **Display**
   - New expense (with receipt link) appears in your existing `daily_expense_categorizer.html` feed.

**Cost hot spots in this flow:**

- The only recurring external cost is **the vision / OCR step**.
- Storage + CPU for 100 receipts / month is effectively free on your own box.

---

## 3.2 Data to Extract (What you pay the model for)

For each receipt, the extractor should aim for:

- **Merchant/Vendor**
  - `merchant_name`
  - Optional: phone, address, website

- **Dates**
  - `transaction_date` (normalized `YYYY-MM-DD`)
  - Optional: `transaction_time` (HH:MM)

- **Line Items**
  - Array of:
    - `quantity`
    - `description`
    - `unit_price`
    - `line_total` (or recompute on backend)

- **Totals**
  - `subtotal`
  - `tax_amount`
  - `total_amount`
  - Optional: `tip_amount`, `discount_amount`

- **Payment**
  - `payment_method` (CASH | CARD | BANK | OTHER)
  - Optional: `last4`, `card_brand` if visible

- **Receipt IDs / Store Info (optional)**
  - `receipt_number` / `invoice_number`
  - `store_location` (city/state or address)
  - `register_id`, `cashier` if available

- **Meta**
  - `currency` (default USD unless we detect otherwise)
  - `model_name`
  - `field_confidence` (per field, if provider gives it)

These fields are cheap in terms of tokens; the **image encoding** is what dominates cost for LLM-style vision models.

---

## 3.3 AI Vision Model Options & Cost Analysis

### 3.3.0 Common assumptions for cost math

To make apples-to-apples comparisons, I’ll make **conservative** assumptions:

- Each receipt = **1 page**, roughly **1024×1024** pixels.
- For multimodal LLMs:
  - ~**1.5k input tokens** (image patches + prompt text)
  - ~**1.0k output tokens** (JSON)
  - ≈ **2.5k tokens per receipt**, rounded to **3k tokens** for safety.
  - For 100 receipts/month → **300k tokens/month**.
- For page-priced OCR services:
  - 1 receipt ≈ 1 **page**.
  - 100 receipts/month = **100 pages**.

All prices below are **approximate** and based on current public pricing pages as of late 2025 – always double-check before you commit.

---

### 3.3.1 OpenAI GPT-4 Vision (modern equivalent: GPT-4o / gpt-4o-mini)

OpenAI’s current “everyday” multimodal model is **GPT-4o** and its cheaper sibling **gpt-4o-mini**, both supporting images. Pricing is now **per token** for text + image, no separate image surcharge. :contentReference[oaicite:0]{index=0}  

**Pricing (gpt-4o-mini, text+vision):** :contentReference[oaicite:1]{index=1}  

- Input: **$0.15 per 1M tokens**
- Output: **$0.60 per 1M tokens**

**Approximate monthly cost for 100 receipts:**

Assume 180k input + 120k output tokens (still within our 300k budget):

- Input: 180k × (0.15 / 1M) ≈ **$0.027**
- Output: 120k × (0.60 / 1M) ≈ **$0.072**
- **Total ≈ $0.10 per 100 receipts**

So basically **ten cents a month** at your current scale.

**Accuracy:**

- GPT-4-level multimodal models do **very well** at receipt/invoice extraction when prompted with a strict JSON schema. Several independent comparisons show GPT-4o with OCR achieving top-tier field extraction on invoices/receipts, rivaling or beating specialized OCR+parser stacks when prompts are tuned. :contentReference[oaicite:2]{index=2}  

**Latency:**

- Typical API latencies: **~1–3 seconds per image** for small prompts (network + model time). That easily fits your **<5s per receipt** requirement.

**Integration complexity:**

- You already know OpenAI’s API pattern from using ChatGPT, but your actual codebase is currently more Gemini-centric.
- Implementation is straightforward: send image bytes + prompt, request JSON output, validate/parse.

**Pros:**

- Very good reasoning, great at messy/low-quality receipts.
- Super cheap at your scale.
- Flexible prompts (e.g., infer missing tax, deduce merchant from logo, etc.).

**Cons:**

- No built-in per-field confidence scores.
- Vendor lock-in unless you abstract a `ReceiptEngine` interface.

---

### 3.3.2 Claude 3 / Claude 3.5/3.7 Sonnet (Vision)

Anthropic’s Claude models (Sonnet/Opus) also support vision. Latest Sonnet variants (3.5 / 3.7) are priced around: :contentReference[oaicite:3]{index=3}  

- Input: **$3 per 1M tokens**
- Output: **$15 per 1M tokens**

**Approximate monthly cost for 100 receipts:**

Using the same 180k in / 120k out assumption:

- Input: 180k × (3 / 1M) ≈ **$0.54**
- Output: 120k × (15 / 1M) ≈ **$1.80**
- **Total ≈ $2.34 per 100 receipts**

Still cheap in absolute terms, but **~23× more expensive than gpt-4o-mini**.

**Accuracy & latency:**

- Independent tests on invoices/receipts show Claude-class models competitive with GPT-4-tier accuracy on field extraction and summarization, with strong reasoning and “follow the schema” behavior. :contentReference[oaicite:4]{index=4}  
- Latency is similar to GPT-4o: ~1–3 seconds per call under normal load.

**Pros:**

- Excellent structured extraction + reasoning.
- Good for cases where you already depend heavily on Anthropic.

**Cons:**

- Higher cost per token.
- Same confidence-score issue: you’d need your own heuristic scoring or a second pass.

---

### 3.3.3 Google Gemini Vision (Gemini 1.5 Flash / 2.5 Flash-Lite)

Google’s **Gemini 1.5 Flash** and the newer **Gemini 2.5 Flash-Lite** are multimodal (text+image) and optimized for speed and low cost. :contentReference[oaicite:5]{index=5}  

Representative pricing (ballpark, text+image):  

- **Gemini 1.5 Flash:** Input ~$0.075/M, Output ~$0.30/M tokens :contentReference[oaicite:6]{index=6}  
- **Gemini 2.5 Flash-Lite:** Input ~$0.10/M, Output ~$0.40/M tokens (similar order of magnitude). :contentReference[oaicite:7]{index=7}  

Let’s use **Gemini 1.5 Flash** (cheaper) as your baseline.

**Approximate monthly cost for 100 receipts (1.5 Flash):**

- Input: 180k × (0.075 / 1M) ≈ **$0.0135**
- Output: 120k × (0.30 / 1M) ≈ **$0.036**
- **Total ≈ $0.05 per 100 receipts**

So this is roughly **half the cost of gpt-4o-mini**, and still very low in absolute terms.

**Accuracy & speed:**

- Google’s own docs and third-party benchmarks show Gemini 1.5 Flash as **very good at structured extraction from documents**, especially when combined with clear JSON schemas. :contentReference[oaicite:8]{index=8}  
- Designed for speed: typical latency can be **sub-second to a couple of seconds** for small images and prompts under good network conditions. :contentReference[oaicite:9]{index=9}  

**Pros:**

- Very cheap per 100 receipts.
- You’re **already integrating Gemini** elsewhere in `/planner/gemini_structured_outputs`, so you can reuse auth + SDK patterns.
- Simple JSON-instructions pattern.

**Cons:**

- Same as other LLMs: no native per-field confidence; you’d compute your own or inspect tokens.

**Net:**
> For *your current stack and volume*, **Gemini 1.5 Flash / 2.5 Flash-Lite is the cleanest, cheapest fit** for an end-to-end “image → JSON” receipt parser.

---

### 3.3.4 Google Cloud Vision API (basic OCR)

This is traditional OCR, not a full semantic parser. You’d get text and layout, then you’d need your own parsing logic (or call an LLM on top of it).

**Pricing (Document Text Detection):**

- Around **$1.50 per 1,000 units**; **first 1,000 units per month are free**. :contentReference[oaicite:10]{index=10}  
- 1 unit ≈ 1 image/page for OCR.

**For 100 receipts/month:**

- **100 units** → **fully inside the free tier**.
- Effective cost: **$0/month**.
- Past the free tier: 100 units ≈ $0.15.

**Accuracy & use case:**

- Text accuracy on high-quality printed text is >98% in many benchmarks. :contentReference[oaicite:11]{index=11}  
- You still need to:
  - segment merchant/amount/etc. from raw text,
  - handle broken layouts, etc.

**Latency:**

- Usually **sub-second to ~1–2 seconds per page**.

**Pros:**

- Essentially free at your volume.
- Very mature OCR.

**Cons:**

- **You still need a parser** (regex + heuristics + maybe a small LLM) to transform OCR text into structured receipt data.
- No native receipt semantics like line items, merchant, totals, etc.

---

### 3.3.5 Google Document AI (Receipt / Invoice Processors)

This is a higher-level Google service specifically for documents like invoices and receipts. It combines OCR with deep learning models to output structured JSON (merchant, totals, line items, etc.). :contentReference[oaicite:12]{index=12}  

**Pricing (approx):**

- Pre-built processors (including **Receipts/Invoices**) are typically around **$0.10 per document** for 1–10 pages, and Google advertises that you get a **free tier (hundreds to ~1000 pages/month)**. :contentReference[oaicite:13]{index=13}  

For your scale:

- **100 receipts/month** → **likely fully covered by the free tier**.
- Even without free tier, 100 × $0.10 = **$10/month**.

**Accuracy:**

- Designed for documents like receipts; extracts:
  - merchant name, transaction date, totals, line items, etc. with confidence scores. :contentReference[oaicite:14]{index=14}  
- Research and user reports show F1 scores in the **90–95%+ range** on standard invoice/receipt datasets, similar to specialized LayoutLMv3 models. :contentReference[oaicite:15]{index=15}  

**Latency:**

- Typically **1–3 seconds per page** depending on load.

**Pros:**

- Structured JSON output with **per-field confidence**, less prompt engineering.
- Fits your **requirements almost out of the box**.
- Free or very cheap for 100 receipts/month.

**Cons:**

- More setup (enable Document AI, create processors, manage service accounts).
- Slightly heavier “enterprise” feeling than direct Gemini calls.
- Different stack than the Gemini API you already have, though still all Google.

---

### 3.3.6 Azure Computer Vision & Azure AI Document Intelligence

Azure has two relevant pieces:

1. **Azure AI Vision (OCR / Read API)**
   - OCR is billed **per 1,000 transactions**, around **$1–$1.50 per 1,000 pages** with free quota. :contentReference[oaicite:16]{index=16}  
   - 100 receipts → effectively **$0** in free tier, or ~$0.10–$0.15 if paying.
   - You’d still need custom parsing.

2. **Azure AI Document Intelligence (formerly Form Recognizer)**  
   - Has a **prebuilt Receipt model** that extracts merchant, date, totals, line items, etc. with structured JSON + confidence. :contentReference[oaicite:17]{index=17}  
   - Pricing for **All Prebuilt Models (Receipt, Invoice, etc.)** is about **$10 per 1,000 pages**, with **first 500 pages/month free**. :contentReference[oaicite:18]{index=18}  

For 100 receipts/month:

- Well within **the 500 pages free tier** → **$0**.
- If you ever went above that:
  - 100 pages = 0.1 × $10 = **$1/month**.

**Accuracy & latency:**

- Similar story to Google Document AI: **high accuracy** for receipts/invoices, including line items and totals. :contentReference[oaicite:19]{index=19}  
- Latency ~1–3 seconds per document.

**Pros:**

- Very strong prebuilt receipt read, just like Google Document AI.
- Free at your volume.
- Good for multi-cloud or Azure-centric shops.

**Cons:**

- You’re not currently on Azure anywhere in this stack.
- Would introduce a whole new cloud provider just for receipts.

---

### 3.3.7 Local / Open Source (Tesseract, OpenCV, LayoutLM, Donut)

**Tesseract + OpenCV:**

- Free, local OCR engine.
- Text accuracy on receipts is **solid but below the big cloud OCRs** (~88–95% depending on image quality). :contentReference[oaicite:20]{index=20}  
- No semantic parsing; you must:
  - preprocess images (deskew, denoise),
  - run Tesseract,
  - parse via regex/rules or a small local model.

**Document Understanding Models (LayoutLMv3, Donut, etc.):**

- **LayoutLMv3** fine-tuned on the **CORD** receipt dataset achieves **F1 ≈ 0.96** on receipt entity extraction. :contentReference[oaicite:21]{index=21}  
- **Donut** (OCR-free transformer for documents) shows SOTA-level performance for many doc-understanding tasks. :contentReference[oaicite:22]{index=22}  
- To use these effectively you typically want:
  - A **GPU** (RTX 3060-class or better) for fast inference.
  - A pipeline to resize and batch images.
  - Potential fine-tuning if your receipts differ a lot from public datasets.

**GPU cost & practicality:**

- A used **RTX 3060 12GB** is currently around **$200–$230** in the US. :contentReference[oaicite:23]{index=23}  
- Power draw under load ≈ **170W**; but for **100 receipts/month**, actual GPU on-time is tiny (seconds to minutes), so electricity cost is negligible.

However, the **real cost** is **engineering time**:

- Installing CUDA / drivers.
- Setting up Hugging Face models, tokenizers, pre/post-processing.
- Implementing health checks, fallbacks, logging, etc.
- Maintaining code as the Python/torch ecosystem churns.

---

### 3.3.8 Side-by-side Summary (100 receipts/month)

**Very rough cost & characteristics (assuming 1 page per receipt):**

| Option                             | Est. Cost / 100 receipts | Accuracy for receipts (qualitative)                         | Typical Latency / image | Engineering Complexity |
|------------------------------------|--------------------------|-------------------------------------------------------------|-------------------------|------------------------|
| **OpenAI gpt-4o-mini (vision)**   | **~$0.10**               | Excellent (LLM reasoning + image)                         | 1–3s                    | Low (simple HTTP API)  |
| **Claude Sonnet (vision)**        | **~$2.34**               | Excellent, comparable to GPT-4-class                     | 1–3s                    | Low                    |
| **Gemini 1.5 Flash / 2.5 Flash-Lite** | **~$0.05**           | Excellent, very strong for structured extraction          | <1–2s                   | Low (and you already use Gemini) |
| **Google Cloud Vision OCR**       | **$0 (in free tier)**    | Very high text accuracy; no semantics out-of-the-box       | <1–2s                   | Medium (need custom parser) |
| **Google Document AI (Receipt/Invoice)** | **$0 (in free tier)** or ~$10 w/o | High; specialized receipt/invoice with confidence scores | 1–3s                    | Medium-High (GCP setup, processors) |
| **Azure OCR + Doc Intelligence**  | **$0 (in free tier)** / ~$1 | High; prebuilt receipt model w/ confidence scores       | 1–3s                    | High (new cloud stack) |
| **Local Tesseract only**          | **$0**                    | Good but below cloud OCR, poor on noisy images             | <1s (local)             | High (need parser + image prep) |
| **Local LayoutLMv3/Donut + GPU**  | **$0 / doc (but ~$200+ GPU)** | SOTA on receipts with right model, on par w/ cloud SOTA | <1s after warm-up       | Very High (ML infra, models, tuning) |

---

### 3.3.9 Recommendation (for *this* project)

**Short answer:**

- For your **current scale (50–100 receipts/month)** and **existing Gemini integration**, I recommend:

> **Primary engine:** _Gemini 1.5 Flash or 2.5 Flash-Lite_  
> **Architecture:** Single-call “image → structured JSON” parser behind a `ReceiptEngine` interface.

**Why:**

1. **Budget:**  
   - 100 receipts/month ≈ **$0.05–$0.10/month** with Gemini Flash. That’s effectively free.

2. **Simplicity:**  
   - You avoid the added friction of configuring Document AI processors or onboarding Azure just for one feature.
   - You can stick to **one cloud SDK** you already have.

3. **Performance & accuracy:**
   - Benchmarks and anecdotal reports show Gemini Flash competitive with GPT-4-class models on document understanding. :contentReference[oaicite:24]{index=24}  
   - It can handle weird layouts, faint text, etc., especially when you let it “look” at the whole image rather than just text.

4. **Future flexibility:**
   - You can later add:
     - A **Document AI / Azure DI engine** for high-volume or compliance scenarios.
     - A **local LayoutLM engine** if you ever truly need to keep everything on-prem.

I’d design `app/services/receipt_parser.py` with a **pluggable engine interface** so you can choose between:

- `GeminiReceiptEngine` (default),
- `OpenAIReceiptEngine`,
- `DocumentAIReceiptEngine`,
- `AzureReceiptEngine`,
- `LocalReceiptEngine`.

…but start with **one engine (Gemini)** to get the feature live quickly.

---

## 3.4 Storage & GPU Feasibility

### 3.4.1 Storage path & compression

Proposed layout (matches your requirement):

- Base path:  
  `/home/adamsl/planner/nonprofit_finance_db/uploads/receipts/`

- Subdirectories by year/month:  
  `/uploads/receipts/2025/11/receipt_20251114T231530Z_originalfilename.jpg`

- Store **relative path** in `Expense.receipt_url`, e.g.:  
  `receipts/2025/11/receipt_20251114T231530Z_cvs_groceries.jpg`

**Formats & limits:**

- Accept: **JPG, PNG, WebP, PDF** (1st page only).
- Max input size: **5MB**.
- On backend:
  - If >5MB, **downscale/compress** using Pillow or similar.
  - Normalize long edge to e.g. **1200–1600 px** – plenty for OCR/LLMs and reduces tokens.

This has no meaningful cost impact at your volume, but **reduces tokens** for multimodal models (cheaper + faster).

---

### 3.4.2 Is it worth buying a GPU just for receipts?

**Short, direct answer:**  
> **No. A GPU is **not** financially or technically justified for **receipt parsing alone** at your current scale.**

Why:

1. **API cost is already trivial.**
   - Even if you picked the “expensive” Claude Sonnet path, you’re at **$2–3/month** for 100 receipts.
   - With Gemini 1.5 Flash or gpt-4o-mini, you’re at **$0.05–$0.10/month**.

2. **GPU upfront + maintenance cost dwarfs that.**
   - A used **RTX 3060 12GB** is about **$200–$230** right now. :contentReference[oaicite:25]{index=25}  
   - You also pay in:
     - Time to set up CUDA/drivers.
     - Engineering complexity running and updating PyTorch/Transformers stacks.
     - Debugging performance / memory issues.

3. **Runtime usage is tiny.**
   - 100 receipts/month at <1s/receipt is **under 2 minutes of GPU time** monthly.
   - Electricity cost is **near zero**.

4. **Open-source models are fantastic, but heavy.**
   - LayoutLMv3 on CORD gives F1 ≈ 0.96 for receipts. :contentReference[oaicite:26]{index=26}  
   - That’s comparable to Google Document AI or Azure DI, but **they give you that with a REST call**, no infra.

**When a GPU might be worth it for you:**

- If you also want to:
  - Run **local LLMs** for other projects.
  - Do **batch VR / 3D / video ML** locally.
  - Train your own models with **your receipts** (e.g., fine-tuning LayoutLMv3 or Donut on your data).
- Even then, it’s about your **overall AI experimentation roadmap**, not this feature.

So: for **this specific receipt scanner**, I’d **not** buy a GPU. Use cloud APIs and keep things simple.

---

## 3.5 Rate Limits & Error Handling at this Scale

Even though your volume is low, design the system to be robust:

- **Rate limits:**
  - All providers have generous per-minute limits; 100 receipts/month won’t touch them.
  - Still, implement:
    - Retry with backoff on **429** and transient 5xx.
    - Request-ID logging to trace failures.

- **Timeouts:**
  - Set client timeouts ~10–15 seconds; typical latency will be 1–3s.

- **Error handling strategy:**
  - If AI parsing fails:
    - Return an error with **human-readable message** and a “Try again” option.
    - Let user upload again or fall back to “manual entry” while still storing the receipt image.
  - Log:
    - model name, status code, timing, truncated prompt/response for debugging.

---

## 3.6 Direct Answers to Your Budget Questions

1. **Which AI vision model do you recommend and why?**  
   - For *this project right now*: **Gemini 1.5 Flash (or 2.5 Flash-Lite)**.  
   - Reasons: you already use Gemini, it’s **very cheap**, fast, and very good at structured extraction from documents.

2. **Estimated cost for 100 receipts/month?**  
   - Gemini 1.5 Flash: **≈ $0.05/month**.  
   - OpenAI gpt-4o-mini: **≈ $0.10/month**.  
   - Claude Sonnet: **≈ $2.34/month**.  
   - Google Document AI / Azure Doc Intelligence: **$0/month** within free tiers (500–1000 pages/month).  
   - Google Vision / Azure OCR only: also effectively **$0/month** at that volume.

3. **Should we implement item-level expense splitting?**  
   - From a **data model** point of view: yes, but you can do it **later**.  
   - For MVP: parse all items but **store them as metadata**, and create a **single Expense row** per receipt. Later, you can add “Split by line item” → multiple Expense records referencing the same `receipt_url`.

4. **How should we handle receipts with currency other than USD?**  
   - Ask the model to **detect currency code** (`USD`, `EUR`, etc.).  
   - Add `currency` to your `Expense` or to `ReceiptMetadata`.  
   - Initially: treat everything as USD unless the model is “very sure” it’s something else (e.g., `€` or `CAD` explicitly).  
   - Later, you can add exchange-rate normalization if needed.

5. **Should we implement receipt image quality validation?**  
   - Yes, but keep it **lightweight**:
     - Simple checks: resolution, size, basic contrast.
     - If the model returns very low confidence or obviously broken output, show:  
       “Receipt may be too blurry or cropped – please retake a clearer photo.”

6. **Best approach for fallback if AI service is unavailable?**  
   - In `ReceiptEngine`:
     1. Try **primary provider** (e.g., Gemini).
     2. On error/timeout:
        - Option A: **Fallback provider** (e.g., Tesseract + simple parser or another LLM).
        - Option B: Log error + prompt user to **enter data manually**, still storing the image.
   - Given your volume, a simple “manual backup” is fine for v1.

7. **Should we track parsing confidence scores for future ML training?**  
   - Yes, if you plan to iterate on this:
     - For LLM-only solutions, you can ask the model to output **per-field confidence 0–1** and store it in a `receipt_metadata` JSON column.
     - For Document AI / Azure DI, they already give you confidences.
   - This lets you:
     - Flag low-confidence fields in the UI.
     - Build your own models later using human-corrected data.

8. **Any privacy/compliance considerations for receipt storage?**  
   - Receipts may contain:
     - Partial card numbers, names, addresses, loyalty IDs.
   - Basic steps:
     - Limit access to `/uploads/receipts/` to **authenticated users** in your org.
     - Ensure backups and logs don’t leak raw images.
     - If you ever handle **donor/beneficiary receipts**, treat them as personal data (PII):
       - Document retention policy (e.g., 7 years then delete).
       - Optionally redact card numbers on images before long-term storage.

---

## 3.7 GPU Decision – Final Word

> **For this receipt scanner feature alone: don’t buy a GPU.**  

If you later decide to:

- run local LLMs,
- experiment with LayoutLMv3/Donut at scale,
- or build heavy VR/vision ML pipelines,

then we can revisit a **GPU build plan** (RTX 3060+), but that’s **a separate, broader AI infra decision**, not a requirement for this receipt parser.

---

**Next step suggestion:**  
When you’re ready, we can move on to **Section 6.2 Backend Implementation** and I’ll define:

- `ReceiptEngine` interface
- `GeminiReceiptEngine` implementation
- `/api/parse-receipt` FastAPI endpoint skeleton
- How to store `receipt_url` + optional `ReceiptMetadata`.

All of that will plug directly into the model choice we just settled on.
