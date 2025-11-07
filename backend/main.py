from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import uuid
import requests
import time
from typing import List, Dict, Optional

load_dotenv()

app = FastAPI(title="BarangayAI", description="AI Support for Barangay Officials")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"  
)

OLLAMA_URL = "http://localhost:11434/api/chat"

# Data Models
class ChatMessage(BaseModel):
    content: str
    role: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: str = "general"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    context_used: str
    ai_source: str
    processing_time: float = 0.0

# ACTION-ORIENTED System Prompts
SYSTEM_PROMPTS = {
    "general": """You are BarangAI, a helpful AI assistant for barangay officials.

**CRITICAL: UNDERSTAND AND EXECUTE USER REQUESTS**

When users ask you to DO something:
1. **ACTUALLY DO IT** - Create the content they requested
2. **Provide the actual output** - Don't just give advice about how to do it
3. **Be specific and actionable** - Give them exactly what they asked for
4. **If you can't do something technical** (like actually send files), explain what you CAN do and provide the content

**EXAMPLES:**
- If they say "make me a presentation about X" → CREATE the presentation outline/content
- If they say "write a letter about Y" → WRITE the actual letter
- If they say "create a formula for Z" → PROVIDE the exact formula
- If they say "compile to PDF and send" → EXPLAIN you can't send files but PROVIDE the content ready for PDF

**RESPONSE STYLE:**
- Be direct and helpful
- Provide actual content, not just advice
- Use clear formatting
- If something isn't possible, explain why and offer alternatives""",

    "excel": """You are an Excel expert. When asked for formulas or spreadsheets:
- PROVIDE THE ACTUAL FORMULAS
- Give specific examples with cell references
- Create sample data if needed
- Explain how to implement""",

    "word": """You help with documents. When asked to create documents:
- WRITE THE ACTUAL DOCUMENT CONTENT
- Use proper formatting
- Include all necessary sections
- Make it ready to use""",

    "presentation": """You create presentations. When asked for slides:
- CREATE THE ACTUAL SLIDE CONTENT
- Use bullet points and structure
- Include speaker notes if helpful
- Make it presentation-ready"""
}

sessions: Dict[str, List[ChatMessage]] = {}

def get_system_prompt(context: str) -> str:
    return SYSTEM_PROMPTS.get(context, SYSTEM_PROMPTS["general"])

class AIService:
    @staticmethod
    def get_available_ollama_models():
        """Get list of available Ollama models"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except:
            return []

    @staticmethod
    def call_deepseek_api(messages: list) -> str:
        """Call DeepSeek API"""
        try:
            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            if "402" in error_str or "Insufficient Balance" in error_str:
                raise Exception("API_INSUFFICIENT_BALANCE")
            else:
                raise e

    @staticmethod
    def call_ollama_chat(messages: list, model: str = "llama3:latest", timeout: int = 25) -> str:
        """Call Ollama using chat endpoint"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1200,
                }
            }
            
            response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            response_text = data.get("message", {}).get("content", "").strip()
            if not response_text:
                raise Exception("Empty response from Ollama")
                
            return response_text
            
        except requests.exceptions.Timeout:
            raise Exception(f"Ollama timeout after {timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama connection error: {str(e)}")

    @staticmethod
    def is_ollama_available() -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get("http://localhost:11434/api/version", timeout=3)
            return response.status_code == 200
        except:
            return False

    @staticmethod
    def get_fallback_response(context: str, message: str) -> str:
        """ACTION-ORIENTED fallback responses that actually DO what users ask"""
        message_lower = message.lower()
        
        # Detect what the user actually wants
        if "pdf" in message_lower and ("compile" in message_lower or "send" in message_lower or "create" in message_lower):
            return """I understand you'd like me to create content and compile it to PDF. While I can't actually send files or create PDFs directly, I CAN create the content ready for you to save as PDF.

Here's what I can do for you:
1. **Create the actual content** you need (documents, presentations, reports)
2. **Format it properly** for PDF conversion
3. **Provide instructions** on how to save it as PDF

What specific content would you like me to create for you? For example:
- "Create a barangay meeting report"
- "Make a presentation about community projects" 
- "Write a letter to municipal officials"

Just tell me what you need, and I'll create it ready for PDF!"""

        elif "presentation" in message_lower and "bullet" in message_lower:
            return """**PRESENTATION: Building a PC for Barangay Office Use**

🎯 **Slide 1: Title Slide**
- **Title**: Building a Cost-Effective PC for Barangay Operations
- **Subtitle**: A Practical Guide for Government Offices
- **Presenter**: [Your Name/Position]
- **Date**: [Presentation Date]

📊 **Slide 2: Agenda**
• Why Build vs Buy?
• Essential Components
• Step-by-Step Assembly
• Software Setup
• Budget Considerations
• Q&A

💡 **Slide 3: Why Build Your Own PC?**
- **Cost Savings**: 20-30% cheaper than pre-built
- **Customization**: Tailor to specific barangay needs
- **Upgradability**: Easy future improvements
- **Understanding**: Better troubleshooting knowledge

🛠️ **Slide 4: Essential Components**
1. **Processor (CPU)**: Intel i3 or AMD Ryzen 3 (Office tasks)
2. **Motherboard**: H610/B550 chipset with enough USB ports
3. **RAM**: 8GB DDR4 (Expandable to 16GB)
4. **Storage**: 256GB SSD + 1TB HDD for documents
5. **Power Supply**: 500W 80+ Bronze certified
6. **Case**: Mid-tower with good airflow

🔧 **Slide 5: Assembly Steps**
**Step 1**: Install CPU on motherboard
**Step 2**: Mount RAM modules
**Step 3**: Install motherboard in case
**Step 4**: Connect power supply cables
**Step 5**: Install storage drives
**Step 6**: Cable management
**Step 7**: First boot and BIOS setup

💻 **Slide 6: Software Setup**
- **OS**: Windows 10/11 or Linux (for budget)
- **Office Suite**: Microsoft Office or LibreOffice
- **Security**: Antivirus + Firewall
- **Backup**: Automated system backups
- **Government Software**: eBPLS, reporting tools

💰 **Slide 7: Budget Breakdown**
- CPU: ₱5,000-7,000
- Motherboard: ₱4,000-5,000  
- RAM: ₱2,000-3,000
- SSD: ₱2,000-3,000
- HDD: ₱2,000-2,500
- PSU: ₱2,500-3,500
- Case: ₱1,500-2,500
- **TOTAL**: ₱19,000-26,500

🎯 **Slide 8: Recommendations for Barangay**
- Start with 2 units for testing
- Train staff on basic maintenance
- Establish backup procedures
- Consider warranty and support

❓ **Slide 9: Q&A**
- Open floor for questions
- Contact information
- Next steps

---
**To save as PDF**: Copy this content to Word or Google Docs, then use File > Save As > PDF"""

        elif "build a pc" in message_lower or "building a computer" in message_lower:
            return """**COMPLETE GUIDE: Building a PC for Barangay Office Use**

I'll create a practical guide that you can use directly.

---

**🛠️ PRACTICAL PC BUILD FOR BARANGAY OFFICE**

**BUDGET: ₱20,000-₱25,000**

**COMPONENTS LIST (with Philippine Prices):**

1. **PROCESSOR**: Intel Core i3-12100 
   - Price: ₱5,500
   - Why: Efficient for office tasks, good integrated graphics

2. **MOTHERBOARD**: MSI H610M-G
   - Price: ₱4,200
   - Why: Reliable brand, enough connectivity

3. **RAM**: TeamGroup T-Force Vulcan 8GB DDR4 3200MHz
   - Price: ₱1,800
   - Why: Good performance, can add another 8GB later

4. **STORAGE**: 
   - SSD: Kingston NV2 256GB NVMe - ₱1,600
   - HDD: Seagate Barracuda 1TB - ₱2,200
   - Why: Fast boot + ample document storage

5. **POWER SUPPLY**: FSP Hyper K 500W 80+ 
   - Price: ₱2,300
   - Why: Reliable brand, sufficient power

6. **CASE**: Tecware Nexus Air M2
   - Price: ₱1,500
   - Why: Good airflow, includes fans

7. **MONITOR**: Any 21.5" 1080p IPS
   - Price: ₱4,500
   - Why: Clear display for documents

**TOTAL ESTIMATED COST: ₱21,600**

---

**🔧 ASSEMBLY INSTRUCTIONS:**

**STEP 1: PREPARATION**
- Work on clean, static-free surface
- Gather all components and tools
- Read motherboard manual

**STEP 2: CPU INSTALLATION**
1. Open CPU socket lever on motherboard
2. Align golden triangle on CPU with socket marker
3. Gently place CPU (NO FORCE needed)
4. Close lever to secure

**STEP 3: RAM INSTALLATION**
1. Open RAM slot clips
2. Align notch on RAM with slot
3. Press firmly until clips snap closed
4. Use slots A2 and B2 for dual channel

**STEP 4: MOTHERBOARD INSTALLATION**
1. Place standoffs in case
2. Install I/O shield
3. Position motherboard
4. Screw in securely (don't overtighten)

**STEP 5: POWER SUPPLY**
1. Install PSU in case
2. Connect 24-pin to motherboard
3. Connect 8-pin CPU power
4. Connect SATA power to drives

**STEP 6: STORAGE**
1. Mount SSD in dedicated slot
2. Mount HDD in drive bay
3. Connect SATA data cables

**STEP 7: FINAL CONNECTIONS**
1. Connect front panel cables (power switch, USB)
2. Connect monitor via HDMI
3. Connect keyboard and mouse

**STEP 8: FIRST BOOT**
1. Power on and enter BIOS (usually DEL key)
2. Check if all components detected
3. Set boot priority to USB
4. Install operating system

---

**💡 FOR BARANGAY USE:**

**SOFTWARE TO INSTALL:**
- Windows 10/11 or Linux Mint
- Microsoft Office/LibreOffice
- Antivirus (Avast Free or Windows Defender)
- Chrome/Firefox browser
- PDF reader
- eBPLS system (if required)

**MAINTENANCE TIPS:**
- Weekly disk cleanup
- Monthly antivirus scans
- Regular Windows updates
- Backup important documents to external drive

**TROUBLESHOOTING COMMON ISSUES:**
- No display: Check monitor cable and RAM seating
- No power: Check front panel connectors
- Beep codes: Consult motherboard manual

---
This guide is ready to use for your barangay PC building project! Would you like me to create any specific documents or presentations based on this?"""

        elif "yes" in message_lower and ("compile" in message_lower or "pdf" in message_lower):
            return """I understand you want me to compile content into a PDF. Let me create something useful for you!

**BARANGAY OFFICE DIGITAL TOOLS GUIDE**

📋 **Document Prepared for PDF Export**

**1. ESSENTIAL SOFTWARE FOR BARANGAY OFFICE**

• **Microsoft Office Suite**
  - Word: Official documents and letters
  - Excel: Budget tracking and reports
  - PowerPoint: Community presentations

• **Web Browser** 
  - Google Chrome or Mozilla Firefox
  - For accessing government online services

• **PDF Reader**
  - Adobe Acrobat Reader (free)
  - For viewing official documents

**2. BASIC COMPUTER MAINTENANCE**

**Weekly Tasks:**
- Run disk cleanup
- Update antivirus definitions
- Backup important files

**Monthly Tasks:**
- Defragment hard drive (if HDD)
- Clean temporary files
- Update software

**3. INTERNET SAFETY PRACTICES**

• Use strong passwords
• Avoid suspicious email links
• Log out of shared computers
• Regular browser cache clearing

**4. EBPLS TROUBLESHOOTING**

**Common Issues:**
- Login problems: Check caps lock, reset password
- Slow performance: Clear browser cache, close other tabs
- Printing issues: Check printer connection, update drivers

**5. CONTACT INFORMATION**

• Municipal IT Support: [Local number]
• DILG Helpdesk: [Regional office contact]
• Emergency technical support: [Backup contact]

---
**TO CREATE PDF:**
1. Copy this content to Microsoft Word
2. Format as needed
3. Go to File > Save As
4. Choose PDF format
5. Save and share!

Would you like me to create a different document or add specific content to this one?"""

        else:
            return f"""I'd be happy to help you with **{message}**!

As BarangayAI, I can:
• Create documents, presentations, and reports
• Provide specific formulas and technical guidance  
• Generate content ready for your use
• Explain complex topics in simple terms

What would you like me to **create** or **explain** for you? Please be specific about what you need, and I'll provide the actual content!"""

@app.get("/")
async def root():
    return {"message": "BarangayAI Backend Running", "status": "active"}

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    start_time = time.time()
    
    try:
        # Create or retrieve session
        session_id = chat_request.session_id or str(uuid.uuid4())
        if session_id not in sessions:
            sessions[session_id] = []
        
        # Add user message to session
        user_message = ChatMessage(role="user", content=chat_request.message)
        sessions[session_id].append(user_message)
        
        # Use action-oriented approach
        system_prompt = get_system_prompt(chat_request.context)
        recent_messages = sessions[session_id][-3:] if len(sessions[session_id]) > 3 else sessions[session_id]
        
        # Build messages for AI
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend([{"role": msg.role, "content": msg.content} for msg in recent_messages])
        
        ai_response = ""
        ai_source = "unknown"
        
        # Try Ollama first
        try:
            print(f"🦙 Attempting Ollama for: {chat_request.message[:50]}...")
            if AIService.is_ollama_available():
                ai_response = AIService.call_ollama_chat(messages, "llama3:latest", timeout=25)
                ai_source = "ollama"
                print(f"✅ Ollama response in {time.time() - start_time:.1f}s")
            else:
                raise Exception("Ollama not available")
                
        except Exception as ollama_error:
            print(f"❌ Ollama failed: {ollama_error}")
            
            # Try DeepSeek as backup
            try:
                print("🌐 Attempting DeepSeek API...")
                ai_response = AIService.call_deepseek_api(messages)
                ai_source = "deepseek_api"
                print(f"✅ DeepSeek response in {time.time() - start_time:.1f}s")
            except Exception as api_error:
                print(f"❌ DeepSeek API failed: {api_error}")
                # Use action-oriented fallback response
                ai_response = AIService.get_fallback_response(chat_request.context, chat_request.message)
                ai_source = "fallback"
                print(f"✅ Using action-oriented fallback")
        
        # Store response
        ai_message = ChatMessage(role="assistant", content=ai_response)
        sessions[session_id].append(ai_message)
        
        processing_time = time.time() - start_time
        
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            context_used=chat_request.context,
            ai_source=ai_source,
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"💥 Error after {processing_time:.1f}s: {e}")
        
        return ChatResponse(
            response=AIService.get_fallback_response(chat_request.context, chat_request.message),
            session_id=chat_request.session_id or str(uuid.uuid4()),
            context_used=chat_request.context,
            ai_source="error",
            processing_time=processing_time
        )

# ... (keep other endpoints the same)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)