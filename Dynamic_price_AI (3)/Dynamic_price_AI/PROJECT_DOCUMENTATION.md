# PriceScope Intelligence System ◈ Master Technical Specification
**Version 2.0.0 | Enterprise Edition**

---

## 📋 Table of Contents
1.  **Project Abstract & Executive Summary**
2.  **The Problem Space: Market Fragmentation**
3.  **High-Level System Architecture**
4.  **Chapter 1: Neural Target Identification (Vision AI)**
5.  **Chapter 2: The Scraper Matrix (Data Acquisition)**
6.  **Chapter 3: Strategic Impersonation & Anti-Bot Bypassing**
7.  **Chapter 4: The Machine Learning Pipeline (Analytics)**
8.  **Chapter 5: Real-Time Communication (SSE Streaming)**
9.  **Chapter 6: Frontend Architecture (Cyber-Scanner UI)**
10. **Chapter 7: Backend API Reference**
11. **Chapter 8: Machine Learning Mathematical Models**
12. **Chapter 9: Deployment & Infrastructure**
13. **Chapter 10: Future Roadmap & Scaling**

---

## 1. Project Abstract & Executive Summary
PriceScope Intelligence is a multi-modal AI system designed for real-time market surveillance. Unlike traditional scrapers that require manual product entry, PriceScope uses custom vision identification to bridge the gap between physical objects and digital market data. It orchestrates a fleet of autonomous scrapers to provide a unified pricing dashboard in under 30 seconds.

---

## 2. The Problem Space: Market Fragmentation
The e-commerce landscape is split across dozens of platforms (Amazon, Flipkart, Reliance, etc.), each with its own obfuscated data structures, bot-detection walls, and pricing updates. For a seller or a savvy consumer, manually checking these is impossible. PriceScope automates this at the speed of light.

---

## 3. High-Level System Architecture
The system follows a **Micro-Modular Architecture**:
-   **Frontend**: React client handling the presentation layer.
-   **Ingress Layer**: FastAPI gateway receiving binary image data.
-   **AI Core**: OpenRouter connection for Vision Analysis.
-   **Data Fleet**: A registry of parallel scrapers using Playwright and Curl-Cffi.
-   **Post-Processor**: Scikit-Learn based ML for normalization and outlier detection.

---

## 4. Chapter 1: Neural Target Identification
### 1.1 The Vision Pipeline
When a user uploads an image, the system doesn't just do a simple OCR. It uses **Gemini 2.0 Flash** via the OpenRouter gateway.
-   **Encoding**: Image is downsampled and encoded in Base64.
-   **Tactical Prompting**: We use a "Surgical Identification Prompt" that forces the AI to output exactly 7 specific JSON keys.
-   **Query Engineering**: The AI generates 3 search vectors (e.g., "Sony WH-1000XM5 Black", "XM5 Headphones Sony", "Sony WH1000XM5 Wireless"). This redundancy ensures that even if one platform's search engine is weak, the others will find the product.

---

## 5. Chapter 2: The Scraper Matrix
### 2.1 Parallel Orchestration
We use Python's `asyncio.gather` and `asyncio.Semaphore` to launch 7 scrapers simultaneously. 
### 2.2 Scraper Modules
-   **AmazonScraper**: Uses complex regex patterns to pull prices from highly obfuscated HTML.
-   **RelianceScraper**: Uses **Playwright Browser Automation** to wait for JavaScript to render the "Member Price".
-   **MeeshoScraper**: Scans for cards and extracts prices by analyzing text nodes directly when class names are obfuscated.

---

## 6. Chapter 3: Strategic Impersonation
### 3.1 TLS Handshake Mimicry
Standard scrapers are blocked because their TLS handshakes identify them as "Python scripts." PriceScope uses **Curl-Cffi** to mimic the TLS fingerprint of a real Chrome Browser (v120+) and Firefox.
### 3.2 User-Agent Rotation
A rotating pool of 50+ modern User-Agents prevents the target platform from identifying the request originating from a script.
### 3.3 The Stealth Fallback
If a direct "Fetch" is blocked, the system transparently switches to a **DuckDuckGo Index Fallback**. It searches the platform *via a search engine*, which caches and serves the results, effectively using their index as a free, unblockable proxy.

---

## 7. Chapter 4: The Machine Learning Pipeline
### 4.1 Data Normalization
Prices come in formats like `₹12,999.00`, `Rs. 13000`, or `12k`. Our custom `normalizer.py` uses aggressive regex and float-casting to convert everything to a clean `float`.
### 4.2 KMeans Price Tiers
The system groups all prices into 3 clusters:
1.  **Budget Tier**: Lowest prices, often from secondary sellers.
2.  **Market Sweet Spot**: Where the majority of sellers are priced.
3.  **Premium Tier**: Official brand stores or high-trust sellers.

---

## 8. Chapter 5: Real-Time Communication
### 5.1 Server-Sent Events (SSE)
Unlike standard REST APIs where the user waits for the entire process to finish, we use **SSE (text/event-stream)**.
-   The moment Vision AI finishes, the UI updates.
-   As each scraper finishes (e.g., Amazon first, Flipkart second), those specific cards "pop" into view.
-   This reduces the "perceived latency" for the user from 30s to effectively 2s.

---

## 9. Chapter 6: Frontend Architecture
### 6.1 Cyber-Scanner Design System
The UI uses **Glassmorphism**:
-   `backdrop-filter: blur(12px)`
-   `background: rgba(255, 255, 255, 0.05)`
-   **CSS Variables** for neon accent colors (`--accent-cyan`, `--accent-green`).
-   Animate.css integration for smooth entry of market cards.

---

## 10. Chapter 7: API Documentation
### `POST /analyze`
- **Input**: `multipart/form-data` with a file field.
- **Output**: An SSE stream yielding JSON events:
  - `status`: Step update.
  - `vision_result`: Product metadata.
  - `scraper_result`: Data for a specific platform.
  - `ml_analysis`: Final recommended strategy.

---

## 11. Chapter 8: ML Mathematical Models
### 8.1 Isolation Forest for Outliers
We use an Isolation Forest with a contamination factor of 0.1. This identifies price listings that are statistically "alone"—e.g., a listing for a laptop at ₹500 which is clearly a scam or error. This protects the final recommendation from being skewed.

---

## 12. Chapter 9: Deployment & Infrastructure
### 9.1 Dockerization
- **Backend Image**: Based on `python:3.11-slim`, includes all Playwright system dependencies.
- **Frontend Image**: Multi-stage build (Node -> Nginx) or dev server.
- **Network**: Private bridge network connecting both services.

---

## 13. Chapter 10: Future Roadmap
1.  **Historical Tracking**: Storing pricing data in a specialized Time-Series DB (like InfluxDB).
2.  **Predictive Analytics**: Using LSTM models to predict *when* a price will drop based on historical trends.
3.  **Telegram/WhatsApp Alerts**: Notifying users when the price hits a certain threshold.

---
*End of Specification. Created for the PriceScope Intelligence Unit by Advanced AI Architectures.*
