#  PriceScope Intelligence Unit

Advanced AI-powered dynamic pricing and product analysis dashboard.

## Docker Deployment (Recommended)

To launch the entire infrastructure (Backend + Frontend) in one command:

1. Ensure **Docker Desktop** is running.
2. Run the helper script:
   ```cmd
   docker-up.bat
   ```
   *Alternatively:*
   ```bash
   docker compose up --build
   ```

##  Components
- **Backend**: FastAPI with Gemini 2.5 & Llama 3.3 for product vision.
- **Frontend**: Vite React with Luxury Cyber-Scanner UI.
- **Node Matrix**: Interconnected via Docker internal network.

##  Requirements
- 1GB+ RAM for Docker containers.
- Valid `backend/.env` with GEMINI and GROQ keys.

---
*Created with PriceScope Intelligence Unit Engine.*
