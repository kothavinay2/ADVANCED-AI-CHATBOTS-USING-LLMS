# Advanced AI Chatbots Using LLMs 🤖

An AI-powered chatbot application built using FastAPI and Groq's LLM integration. The project provides an interactive chat interface that supports text conversations, document processing, file uploads, and image analysis using large language models.

## ✨ Features

- **AI-Powered Conversations:** Generate responses using Llama 3.3 70B.
- **Image Analysis:** Process and analyze images using Llama 3.2 90B Vision.
- **Document Processing:** Extract and process text from PDF and Word documents.
- **File Uploads:** Support for multiple file formats and image handling.
- **Modern UI:** Responsive landing page and chat interface with animations.
- **Chat History:** Maintain conversation history and session persistence.
- **Markdown Rendering:** Display formatted text, code blocks, and syntax-highlighted code.
- **Code Copying:** Copy generated code directly from chat responses.
- **FastAPI Backend:** Handle requests through API endpoints.
- **Responsive Design:** Optimized for desktop and mobile devices.

## 🛠️ Technologies Used

- Python
- FastAPI
- Groq API
- Llama 3.3 70B
- Llama 3.2 90B Vision
- HTML, CSS, and JavaScript
- PDF and Word document processing libraries
- Base64 encoding for image handling

## ⚙️ Project Workflow

1. **User Input:** The user submits a message or uploads a supported file.
2. **Request Processing:** The FastAPI backend receives and processes the request.
3. **AI Integration:** The application sends the relevant input to the appropriate Groq-hosted Llama model.
4. **Response Generation:** The model generates a response based on the input and system instructions.
5. **Response Display:** The frontend displays the response with Markdown formatting and code highlighting when applicable.
6. **Session Management:** Conversation history can be maintained across interactions.

## 📂 Project Structure

The exact directory structure may vary depending on your implementation.

```text
ADVANCED-AI-CHATBOTS-USING-LLMS/
├── main.py
├── templates/
│   ├── landing.html
│   └── index.html
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── data/
│   └── chats.json
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## 🚀 Installation and Setup

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd ADVANCED-AI-CHATBOTS-USING-LLMS
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Groq API key

Create a `.env` file in the project root and add your API key:

```env
GROQ_API_KEY=your_groq_api_key
```

Get an API key from [Groq Console](https://console.groq.com/).

Keep your API key private. Never commit your `.env` file to GitHub.

### 5. Run the application

For a FastAPI application whose entry point is `main.py` and whose FastAPI instance is named `app`, run:

```bash
uvicorn main:app --reload
```

If your Python filename or FastAPI instance name differs, adjust the command accordingly.

Open the local URL shown in the terminal, commonly `http://127.0.0.1:8000`.

## 🔐 Security Considerations

- Store API keys in environment variables.
- Exclude `.env` and sensitive files from version control.
- Validate uploaded files and restrict allowed file types and sizes.
- Handle API errors and invalid user inputs safely.
- Configure production deployment settings before public release.

## 🔮 Future Enhancements

- Add retrieval-augmented generation (RAG) for question answering over uploaded documents.
- Improve conversation memory and session management.
- Support additional language models and file formats.
- Add authentication and user-specific chat history.
- Deploy the application to a cloud platform.

## 🎯 Project Objective

The objective of this project is to demonstrate how large language models can be integrated into a web application to build intelligent conversational systems that support natural-language interactions, document processing, and image understanding.

## 👨‍💻 Author

**Kotha Vinay**

## 📄 License

Choose an appropriate open-source license before publishing this project publicly.
