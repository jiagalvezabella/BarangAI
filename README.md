# BarangayAI 🤖
### Real-time AI Support System for Barangay Officials' Digital Literacy

A thesis project providing AI-powered digital literacy support for Filipino barangay officials through an intelligent chat interface.

## 🚀 Features
- **AI-Powered Assistance**: Real-time help for digital tasks using local (Ollama) and cloud AI (DeepSeek)
- **Multiple Contexts**: Specialized support for Excel, Word, eBPLS, and general digital literacy
- **User-Friendly Interface**: Clean chat interface designed for non-technical users
- **Session Management**: Persistent conversation history
- **Fast Response Times**: Optimized AI responses with fallback systems

## 🛠️ Tech Stack
- **Backend**: FastAPI, Python
- **Frontend**: HTML5, CSS3, JavaScript
- **AI Integration**: Ollama (Llama3), DeepSeek API
- **Architecture**: REST API with real-time chat

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- Ollama
- Git

# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/BarangayAI.git
cd BarangayAI

# 2. Setup backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. Setup AI (Ollama)
ollama pull llama3:latest
ollama serve

# 4. Run backend
python -m uvicorn main:app --reload --port 8000

# 5. Open frontend
cd ../frontend
# Open index.html in your browser
