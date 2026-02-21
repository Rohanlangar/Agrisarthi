# AgriSarthi Backend (Django API)

[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Supabase](https://img.shields.io/badge/Supabase-Backend%20as%20a%20Service-green)](https://supabase.com/)

AgriSarthi is a voice-first, AI-powered backend API designed to simplify government scheme access for Indian farmers. It enables natural language interactions (Hindi, Marathi, English) to check eligibility, apply for schemes, and track application status. This backend powers the AgriSarthi mobile application.

## 🌟 Key Features

### 🗣️ Voice-Powered Core
- **Multilingual Intent Recognition**: Understands voice commands in Hindi, Marathi, and English using advanced NLP.
- **Contextual Conversations**: Generates human-like responses tailored to the farmer's query.
- **Action Execution**: Directly processes actions like "Applying for PM Kisan" via voice commands.

### 🚜 Farmer-Centric Modules
- **Secure Authentication**: Phone-based OTP login (via Supabase/Twilio).
- **Profile Management**: Detailed farmer profiles including land holdings, crop types, and location.
- **Document Vault**: Secure upload and verification of critical documents (Aadhaar, 7/12, etc.) to dedicated storage buckets.
- **Smart Scheme Engine**: Automated eligibility checking against farmer profiles.
- **Status Tracking**: Real-time updates on application processing stages.

### 🛠 Technical Architecture
- **Framework**: Django & Django REST Framework (DRF).
- **Database & Storage**: Supabase (PostgreSQL & Object Storage).
- **Authentication**: JWT & OTP-based secure flow.
- **Scalability**: Designed for cloud deployment (Render/Heroku compatible).

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Supabase Account
- Git

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/agrisarthi-backend.git
   cd agrisarthi-backend
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   ALLOWED_HOSTS=*
   
   # Database
   DATABASE_URL=postgresql://postgres:password@db.supabase.co:5432/postgres
   
   # Supabase Credentials
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-role-key
   
   # AI/LLM Keys (Optional for advanced NLP)
   OPENAI_API_KEY=sk-...
   GROQ_API_KEY=gsk_...
   ```

5. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start Server**
   ```bash
   python manage.py runserver
   ```
   Access API at `http://127.0.0.1:8000/`.

## 📚 API Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Auth** | `/api/auth/send-otp/` | Request login OTP |
| **Auth** | `/api/auth/verify-otp/` | Verify OTP & get JWT |
| **User** | `/api/farmers/profile/` | Get/Update Farmer Profile |
| **Docs** | `/api/documents/` | Upload/List Farmer Documents |
| **Schemes** | `/api/schemes/` | List all government schemes |
| **Schemes** | `/api/schemes/eligible/` | List schemes farmer is eligible for |
| **Apply** | `/api/applications/` | Submit new application |
| **Voice** | `/api/voice/process/` | Process natural language command |

## 🧪 Testing

Run standard Django tests:
```bash
python manage.py test
```

Test the voice intent parser independently:
```bash
python manage.py shell
>>> from voice.services.intent_parser import IntentParser
>>> print(IntentParser.parse("मुझे पीएम किसान योजना चाहिए", "hindi"))
```

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
