import uuid
import os
import base64
import io
import json
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import FastAPI, Request, UploadFile, File, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from PIL import Image
import PyPDF2
import docx

app = FastAPI()

# Static files for uploads
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("data", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# -----------------------
# Groq LLM Initialization
# -----------------------

# Text model
llm_text = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    max_tokens=4096,
    groq_api_key=GROQ_API_KEY
)

# Vision model for images
llm_vision = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.7,
    max_tokens=4096,
    groq_api_key=GROQ_API_KEY
)

# -----------------------
# Chat Storage
# -----------------------

CHATS_FILE = "data/chats.json"

def load_chats() -> Dict:
    """Load all chats from file"""
    if os.path.exists(CHATS_FILE):
        try:
            with open(CHATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_chats(chats: Dict):
    """Save all chats to file"""
    with open(CHATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)

def get_chat_title(messages: List[Dict]) -> str:
    """Generate chat title from first user message"""
    for msg in messages:
        if msg.get("role") == "user":
            text = msg.get("content", "")
            if isinstance(text, str):
                text = text.strip()
            else:
                text = str(text) if text else ""
            if text:
                # Remove file upload notation for title
                text = text.split("\n\n[Image(s) uploaded:")[0]
                text = text.split("\n\nI've uploaded")[0]
                return text[:50] + "..." if len(text) > 50 else text
    return "New Chat"

# In-memory session for active chats
session_memory: Dict[str, List[Dict]] = {}
UPLOAD_FOLDER = "uploads"

# Allowed file types - images accepts all common formats
ALLOWED_DOCUMENTS = {'.pdf', '.docx', '.doc', '.txt', '.csv', '.json', '.md'}
ALLOWED_IMAGES = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif', '.svg', '.ico', '.heic', '.heif', '.raw', '.cr2', '.nef', '.arw', '.dng', '.orf', '.raf', '.pef', '.rw2'}

# -----------------------
# Helper Functions
# -----------------------

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read().strip()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def process_document(file_path: str, filename: str) -> str:
    """Process different document types and extract text"""
    ext = os.path.splitext(filename.lower())[1]
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    else:
        return extract_text_from_txt(file_path)

def encode_image_to_base64(image_path: str) -> str:
    """Convert image to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def is_image_file(filename: str) -> bool:
    """Check if file is an image based on extension"""
    ext = os.path.splitext(filename.lower())[1]
    image_extensions = ALLOWED_IMAGES | {'.avif', '.apng', '.jfif', '.pjpeg', '.pjp'}
    return ext in image_extensions or filename.lower().endswith(('.jpg', '.jpeg'))

def truncate_text(text: str, max_length: int = 15000) -> str:
    """Truncate text to fit within token limits"""
    if len(text) > max_length:
        return text[:max_length] + "\n\n[Document truncated due to length...]"
    return text


# -----------------------
# Chat Endpoint
# -----------------------

@app.post("/chat")
async def chat(
    session_id: str = Form(...),
    message: str = Form(...),
    files: List[UploadFile] = File(default=[])
):
    """Handle chat with text, documents, and images"""
    
    # Initialize session if new
    if session_id not in session_memory:
        session_memory[session_id] = []
    
    conversation = session_memory[session_id]
    
    # Process uploaded files
    document_context = ""
    image_data_list = []
    uploaded_files_info = []
    
    for file in files:
        if not file.filename:
            continue
            
        ext = os.path.splitext(file.filename.lower())[1]
        file_path = f"{UPLOAD_FOLDER}/{uuid.uuid4()}_{file.filename}"
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        uploaded_files_info.append({"name": file.filename, "path": file_path})
        
        # Process based on file type
        if ext in ALLOWED_DOCUMENTS:
            # Extract text from document
            extracted_text = process_document(file_path, file.filename)
            document_context += f"\n\n--- Content from {file.filename} ---\n{truncate_text(extracted_text)}"
            
        elif ext in ALLOWED_IMAGES:
            # Prepare image for vision model
            base64_image = encode_image_to_base64(file_path)
            image_data_list.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/{ext[1:]};base64,{base64_image}"}
            })
    
    # Build the user message content - for history, use simple text
    full_text = message
    if document_context:
        full_text += f"\n\nI've uploaded the following documents:\n{document_context}"
    
    # For LLM API call, use structured format if images present
    if image_data_list:
        message_content = [{"type": "text", "text": full_text}]
        message_content.extend(image_data_list)
    else:
        message_content = full_text
    
    # Add to conversation history as simple text (for consistent history storage)
    history_text = full_text
    if image_data_list:
        history_text += f"\n\n[Image(s) uploaded: {len(image_data_list)} image(s)]"
    conversation.append({"role": "user", "content": history_text})
    
    # Keep only last 10 messages to manage context
    conversation = conversation[-10:]
    
    # Prepare messages for LLM
    system_message = SystemMessage(content="""You are a helpful AI assistant. You can:
1. Answer questions and have conversations
2. Analyze images and describe what you see
3. Read and summarize documents (PDF, Word, text files)
4. Extract information from uploaded files

Be concise but thorough. If a user uploads documents, refer to their content. If they upload images, describe what you see.""")
    
    # Convert conversation to LangChain message format
    # Only include text content in history; images are handled in the current message only
    messages = [system_message]
    
    for msg in conversation[:-1]:  # All messages except current (last) one
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    
    # Add current user message with images if present
    messages.append(HumanMessage(content=message_content))
    
    # Choose model based on whether images are present
    llm = llm_vision if image_data_list else llm_text
    
    # Get response
    try:
        response = llm.invoke(messages)
        answer = response.content
        
        # Add assistant response to history
        conversation.append({"role": "assistant", "content": answer})
        session_memory[session_id] = conversation
        
        # Save to persistent storage
        chats = load_chats()
        if session_id in chats:
            chats[session_id]["messages"] = conversation
            chats[session_id]["updated_at"] = datetime.now().isoformat()
            # Update title on first message
            if len(conversation) == 2 and chats[session_id]["title"] == "New Chat":
                chats[session_id]["title"] = get_chat_title(conversation)
            save_chats(chats)
        
        return JSONResponse({
            "success": True,
            "answer": answer,
            "files_processed": len(uploaded_files_info)
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "answer": "Sorry, I encountered an error processing your request."
        }, status_code=500)


# -----------------------
# Chat Management Endpoints
# -----------------------

@app.get("/api/chats")
async def list_chats():
    """List all saved chats"""
    chats = load_chats()
    chat_list = []
    for chat_id, chat_data in chats.items():
        chat_list.append({
            "id": chat_id,
            "title": chat_data.get("title", "New Chat"),
            "created_at": chat_data.get("created_at", ""),
            "updated_at": chat_data.get("updated_at", ""),
            "message_count": len(chat_data.get("messages", []))
        })
    # Sort by updated_at descending
    chat_list.sort(key=lambda x: x["updated_at"], reverse=True)
    return JSONResponse({"chats": chat_list})

@app.post("/api/chats")
async def create_chat():
    """Create a new chat"""
    chat_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    chats = load_chats()
    chats[chat_id] = {
        "id": chat_id,
        "title": "New Chat",
        "messages": [],
        "created_at": now,
        "updated_at": now
    }
    save_chats(chats)
    session_memory[chat_id] = []
    return JSONResponse({
        "success": True,
        "chat": {
            "id": chat_id,
            "title": "New Chat",
            "created_at": now,
            "updated_at": now
        }
    })

@app.get("/api/chats/{chat_id}")
async def get_chat(chat_id: str):
    """Get a specific chat with messages"""
    chats = load_chats()
    if chat_id not in chats:
        return JSONResponse({"success": False, "error": "Chat not found"}, status_code=404)
    
    chat_data = chats[chat_id]
    # Load into session memory
    session_memory[chat_id] = chat_data.get("messages", [])
    
    return JSONResponse({
        "success": True,
        "chat": {
            "id": chat_id,
            "title": chat_data.get("title", "New Chat"),
            "messages": chat_data.get("messages", []),
            "created_at": chat_data.get("created_at", ""),
            "updated_at": chat_data.get("updated_at", "")
        }
    })

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a chat"""
    chats = load_chats()
    if chat_id in chats:
        del chats[chat_id]
        save_chats(chats)
    if chat_id in session_memory:
        del session_memory[chat_id]
    return JSONResponse({"success": True, "message": "Chat deleted"})

@app.put("/api/chats/{chat_id}/title")
async def update_chat_title(chat_id: str, title: str = Form(...)):
    """Update chat title"""
    chats = load_chats()
    if chat_id in chats:
        chats[chat_id]["title"] = title
        chats[chat_id]["updated_at"] = datetime.now().isoformat()
        save_chats(chats)
        return JSONResponse({"success": True})
    return JSONResponse({"success": False, "error": "Chat not found"}, status_code=404)


# -----------------------
# Clear Chat Endpoint
# -----------------------

@app.post("/clear-chat")
async def clear_chat(session_id: str = Form(...)):
    """Clear conversation history"""
    if session_id in session_memory:
        session_memory[session_id] = []
    return JSONResponse({"success": True, "message": "Chat history cleared"})


# -----------------------
# Get Chat History
# -----------------------

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history"""
    history = session_memory.get(session_id, [])
    return JSONResponse({"history": history})


# -----------------------
# Home Page
# -----------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    session_id = str(uuid.uuid4())
    
    # Create the chat entry immediately in backend
    chats = load_chats()
    now = datetime.now().isoformat()
    chats[session_id] = {
        "id": session_id,
        "title": "New Chat",
        "messages": [],
        "created_at": now,
        "updated_at": now
    }
    save_chats(chats)
    session_memory[session_id] = []
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "session_id": session_id
        }
    )


# -----------------------
# Run Server
# -----------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)