# Capstone Project UNFC - Architecture Overview

Based on the project structure and the services you've deployed, here's how Render, Supabase, and Vercel relate to your "capstone_project_unfc" project.

## Overall Project Architecture
This appears to be a **full-stack financial data analysis application** with separate concerns handled by each platform:

- **Frontend (User Interface)**: Hosted on **Vercel**
- **Backend (API & Business Logic)**: Hosted on **Render**
- **Database & Backend Services**: Managed via **Supabase**

## Specific Roles and Relations

### 1. Vercel (Frontend Deployment)
- Hosts your React/Vite-based web application (`frontend/` directory)
- Provides the user interface for data visualization, charts, and interactions
- Deployed from your GitHub repo's `Mateo` branch
- Accessible at: `https://capstone-project-unfc-ashen.vercel.app`
- **Relation**: This is the client-side app that users interact with directly in their browsers

### 2. Render (Backend API Hosting)
- Runs your Python FastAPI application (`backend/app/main.py`)
- Handles server-side logic, data processing, and API endpoints
- Connects to external data sources (like yfinance for stock data)
- Deployed from GitHub, accessible at: `https://capstone-project-unfc-l68p.onrender.com`
- **Relation**: Serves as the API layer that the frontend calls for data and computations

### 3. Supabase (Database & Backend Services)
- Provides PostgreSQL database with migrations (`supabase/migrations/`)
- Stores application data (likely financial predictions, user data, etc.)
- Includes built-in features like authentication, real-time subscriptions, and edge functions
- Project ID: `bizvuwbipvhzguiszcry` ("unfc_capstone_project")
- **Relation**: Acts as the data persistence layer that the backend (on Render) reads from/writes to

## How They Work Together
- **Data Flow**: Frontend (Vercel) → API calls → Backend (Render) → Database queries → Supabase
- **Deployment Flow**: Code changes in GitHub trigger automatic deployments on all three platforms
- **Separation of Concerns**:
  - Vercel: UI/UX and client-side logic
  - Render: Server-side processing and API logic
  - Supabase: Data storage and backend services

This architecture allows for scalable, maintainable development where each service can be updated independently. The frontend handles user interactions, the backend processes complex operations, and Supabase manages data reliably.