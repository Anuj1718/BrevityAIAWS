# TABLE OF CONTENTS
(Leave empty for auto-generation in your Word Processor)

# LIST OF ABBREVIATIONS
- **AI**: Artificial Intelligence
- **NLP**: Natural Language Processing
- **OCR**: Optical Character Recognition
- **API**: Application Programming Interface
- **TTS**: Text-to-Speech
- **UI**: User Interface
- **SDLC**: Software Development Life Cycle
- **TF-IDF**: Term Frequency-Inverse Document Frequency
- **LSA**: Latent Semantic Analysis

# LIST OF FIGURES
*(To be filled in Word after pasting screenshots)*

# LIST OF TABLES
*(To be filled in Word)*

---

# CHAPTER 1 INTRODUCTION

## 1.1 Overview
In today's fast-paced world, professionals, students, and researchers are often overwhelmed by the sheer volume of textual data, particularly in the form of lengthy PDF documents. Brevity AI is a full-stack, AI-powered web application designed to alleviate this information overload. It serves as an intelligent platform for extracting, summarizing, and translating PDF documents with multi-language support (English, Hindi, and Marathi). The platform can handle both searchable PDFs and scanned documents via advanced Optical Character Recognition (OCR), providing users with concise, meaningful summaries using state-of-the-art Natural Language Processing (NLP) and machine learning models.

## 1.2 Motivation
The primary motivation behind Brevity AI is the increasing need for efficient information consumption. Traditional reading of extensive documents is time-consuming. While there are existing summarization tools, many lack support for regional languages like Hindi and Marathi, struggle with scanned documents, or fail to offer different summarization techniques tailored to user needs. Brevity AI bridges this gap by integrating Extractive, Abstractive, and Hybrid summarization methods, along with regional language translation and Text-to-Speech (TTS), making information more accessible and inclusive.

## 1.3 Problem Definition and Objectives
**Problem Definition:**
Users struggle to quickly grasp the core concepts of lengthy or scanned PDF documents. Existing solutions often lack robust regional language support, accurate OCR for scanned files, and versatile summarization options.

**Objectives:**
1. To develop a web application capable of uploading and processing PDF documents up to 300MB.
2. To extract text from both standard and scanned PDFs using intelligent OCR.
3. To provide three modes of summarization: Extractive, Abstractive, and Hybrid.
4. To implement multi-language support, allowing translation of summaries into Hindi and Marathi.
5. To provide Text-to-Speech (TTS) capabilities for audio playback of summaries.

## 1.4 Project Scope & Limitations
**Scope:**
- Processing of standard and scanned PDF documents.
- Multi-lingual text extraction and translation (English, Hindi, Marathi).
- Integration of multiple machine learning models (TextRank, BART, T5).
- Web-based user interface accessible across devices.
- Secure user authentication using Firebase.

**Limitations:**
- Hardware intensive: Abstractive summarization requires significant computational power or GPU acceleration.
- OCR accuracy depends on the quality of the scanned document.
- File size limit of 300MB to manage server load.
- Initial support is limited to three languages (English, Hindi, Marathi).

## 1.5 Methodologies of Problem-Solving
The project employs a component-based methodology:
1. **Document Processing Layer:** PyMuPDF for text extraction and Tesseract OCR for scanned images.
2. **Text Preprocessing:** NLTK for stopword removal, tokenization, and normalization.
3. **Summarization Engine:** Utilizing scikit-learn for Extractive methods (TF-IDF, LSA) and Hugging Face Transformers for Abstractive methods (BART).
4. **Translation & TTS:** Utilizing Helsinki-NLP/T5 models for translation and web audio APIs for TTS.
5. **Frontend/Backend Separation:** React for the UI and FastAPI for asynchronous API handling, ensuring non-blocking processing.

---

# CHAPTER 2 LITERATURE SURVEY
*(This section should ideally contain summaries of 3-5 research papers related to your project domain. Here is a generic placeholder you can expand upon)*

1. **Extractive Text Summarization Techniques:** Many studies have utilized statistical and graph-based methods like TextRank and TF-IDF for extractive summarization. These methods are fast and reliable as they pull exact sentences from the text, prioritizing term frequency.
2. **Abstractive Summarization using Deep Learning:** Recent advancements in Transformer architectures (like BART and T5) have shown superior performance in generating human-like abstractive summaries by understanding context rather than just keyword frequency.
3. **Optical Character Recognition in Regional Languages:** Tesseract OCR has been widely studied for its effectiveness in recognizing complex scripts like Devanagari (used in Hindi and Marathi), though pre-processing of images remains a critical step for high accuracy.
4. **Conclusion of Survey:** The literature suggests that a hybrid approach—combining the factual accuracy of extractive methods with the fluency of abstractive methods—yields the best results for end-users, which is the approach adopted by Brevity AI.

---

# CHAPTER 3 SOFTWARE REQUIREMENTS SPECIFICATION

## 3.1 Assumptions and Dependencies
- **Assumptions:** Users have a modern web browser and a stable internet connection. Uploaded PDFs are not password-protected.
- **Dependencies:** Availability of Hugging Face model APIs/weights, Firebase authentication services, and Tesseract OCR installation on the hosting server.

## 3.2 Functional Requirements
### 3.2.1 System Feature 1: PDF Upload and Text Extraction
- The system must allow users to upload PDF files via drag-and-drop or file selection.
- The system must automatically detect if the PDF is scanned or text-based.
- The system must extract text using OCR if the document is scanned.

### 3.2.2 System Feature 2: Summarization and Translation
- The system must offer Extractive, Abstractive, and Hybrid summarization options.
- The system must allow users to translate the generated summary into Hindi or Marathi.
- The system must provide a Text-to-Speech feature to read the summary aloud.

## 3.3 External Interface Requirements
### 3.3.1 User Interfaces
- A responsive, modern web interface built with React.
- Drag-and-drop file upload component.
- Dashboard for viewing upload progress and processing status.

### 3.3.2 Hardware Interfaces
- None specific to the user. Server requires adequate RAM and preferably a GPU for transformer model inference.

### 3.3.3 Software Interfaces
- Firebase API for Authentication.
- Hugging Face Transformers library for NLP models.
- Tesseract OCR engine.

### 3.3.4 Communication Interfaces
- HTTP/HTTPS protocols for client-server communication using REST APIs.

## 3.4 Nonfunctional Requirements
### 3.4.1 Performance Requirements
- The UI should load in under 3 seconds.
- Extractive summarization should process within seconds; Abstractive summarization may take longer but must provide a real-time progress indicator.

### 3.4.2 Safety Requirements
- Uploaded documents must be stored temporarily and securely, preventing unauthorized access to user data.

### 3.4.3 Security Requirements
- Secure user authentication and session management via Firebase.
- HTTPS encryption for data in transit.

### 3.4.4 Software Quality Attributes
- **Scalability:** The backend (FastAPI) should handle multiple requests asynchronously.
- **Maintainability:** Modular code structure separating routers, services, and ML models.

## 3.5 System Requirements
### 3.5.1 Database Requirements
- Firebase Firestore for user metadata and document processing history.

### 3.5.2 Software Requirements (Platform Choice)
- **Frontend:** React 19, Vite, React Router.
- **Backend:** Python 3.11+, FastAPI, Uvicorn.
- **AI/ML:** PyTorch, Transformers, NLTK, scikit-learn.

### 3.5.3 Hardware Requirements
- **Server:** Minimum 8GB RAM, multi-core CPU. GPU recommended for transformer models.
- **Client:** Any device with a modern web browser.

## 3.6 Analysis Models: SDLC Model to be applied
**Agile Methodology:** The project was developed using the Agile SDLC model. This allowed for iterative development, starting with basic extractive summarization, then adding OCR, followed by abstractive summarization, and finally multi-language support. Continuous testing and integration ensured each module functioned correctly before moving to the next sprint.

---

# CHAPTER 4 SYSTEM DESIGN
*(Note: You will need to draw/generate actual diagrams and paste them in your Word document for this section)*

## 4.1 System Architecture
Brevity AI uses a client-server architecture. The React frontend communicates via REST APIs to the FastAPI backend. The backend delegates tasks to specific service modules (Extractor, Cleaner, Summarizer, Translator). AI models are loaded into memory or accessed via pipelines, and Firebase manages user states.

## 4.3 Data Flow Diagrams
- **Level 0 (Context Diagram):** User -> Uploads PDF -> Brevity AI System -> Returns Summary/Audio.
- **Level 1:** User -> UI -> API Gateway (FastAPI) -> PDF Extractor -> Text Cleaner -> ML Summarizer -> Translator -> UI.

## 4.5 UML Diagrams
- **Use Case Diagram:** Actors (User, System). Use cases (Upload PDF, Select Summarization Type, Translate, Play Audio, Login/Logout).
- **Activity Diagram:** Start -> Login -> Upload Document -> Check if Scanned (If yes, run OCR) -> Extract Text -> Clean Text -> Generate Summary -> Optional Translation -> End.

---

# CHAPTER 5 PROJECT PLAN

## 5.1 Project Estimate
- **Development Time:** ~3-4 months.
- **Cost:** Primarily hosting costs (AWS/Render/Vercel) and domain registration. Software tools used are mostly open-source.

## 5.2 Risk Management
- **Risk:** High memory consumption by AI models leading to server crashes.
  **Mitigation:** Implement LRU caching, use chunked processing, and provide extractive fallbacks.
- **Risk:** Poor OCR accuracy for low-quality scans.
  **Mitigation:** Integrate OpenCV image preprocessing before feeding to Tesseract.

## 5.3 Project Schedule
1. **Month 1:** Requirement gathering, UI/UX design, basic frontend setup, basic FastAPI backend.
2. **Month 2:** PyMuPDF integration, basic Extractive summarization, Firebase auth.
3. **Month 3:** OCR integration, Abstractive summarization (BART), Translation models.
4. **Month 4:** Testing, UI polishing, deployment (AWS/Vercel), report writing.

## 5.4 Team Organization
*(Fill in your team member names and roles here)*
- Team Member 1: Frontend and UI/UX Integration
- Team Member 2: Backend API and Architecture
- Team Member 3: Machine Learning and OCR Pipelines

---

# CHAPTER 6 PROJECT IMPLEMENTATION

## 6.1 Overview of Project Modules
1. **Authentication Module:** Handles user sign-up, login, and secure routing using Firebase.
2. **File Processing Module:** Manages file uploads, validates file types, and handles temporary storage.
3. **Extraction & OCR Module:** Uses PyMuPDF for standard text and Tesseract with OpenCV preprocessing for scanned images.
4. **Summarization Engine:**
   - *Extractive:* Uses NLTK and scikit-learn (TextRank, TF-IDF, LSA).
   - *Abstractive:* Uses Hugging Face `facebook/bart-large-cnn`.
5. **Translation & TTS Module:** Uses Helsinki-NLP/T5 models for translation and browser-based synthesis for TTS.

## 6.2 Tools and Technologies used
- **Frontend:** React, Vite, React Router, Lottie (animations).
- **Backend:** Python, FastAPI, Uvicorn.
- **Machine Learning:** PyTorch, Hugging Face Transformers, NLTK, scikit-learn.
- **Utilities:** Tesseract OCR, PyMuPDF, OpenCV.
- **Deployment:** Vercel (Frontend), Render/AWS (Backend).

## 6.3 Algorithm details
- **TextRank Algorithm:** A graph-based ranking model for text processing. Sentences are represented as vertices, and similarities between sentences are represented as edges. It ranks sentences based on their structural importance in the text.
- **BART (Bidirectional and Auto-Regressive Transformers):** A denoising autoencoder for pretraining sequence-to-sequence models. It reads the entire text bidirectionally and auto-regressively generates the summary, allowing for high-quality abstractive summarization.

---

# CHAPTER 7 SOFTWARE TESTING

## 7.1 Types of Testing
- **Unit Testing:** Testing individual functions (e.g., text cleaning utility, single endpoint).
- **Integration Testing:** Ensuring the backend API correctly receives files from the frontend, processes them, and returns the response.
- **Performance Testing:** Uploading large PDFs (up to 300MB) to ensure the server handles chunking and parallel processing without timing out.
- **Usability Testing:** Gathering feedback on the UI/UX from peers to improve the drag-and-drop interface and progress indicators.

## 7.2 Test Case Result
| Test Case ID | Description | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| TC01 | User Login via Firebase | User successfully logs in | User successfully logs in | Pass |
| TC02 | Upload searchable PDF | Text is extracted instantly | Text is extracted instantly | Pass |
| TC03 | Upload scanned PDF | OCR activates and extracts text | OCR extracts text correctly | Pass |
| TC04 | Generate Abstractive Summary | Concise summary is returned | Summary generated successfully | Pass |
| TC05 | Translate to Marathi | Summary translates accurately | Summary translated | Pass |
| TC06 | File > 300MB upload | System rejects file | System shows error message | Pass |

---

# CHAPTER 8 RESULTS

## 8.1 Outcomes
The Brevity AI platform was successfully developed and deployed. It accurately identifies scanned vs. searchable documents, applies intelligent OCR where necessary, and produces highly coherent summaries using both extractive and abstractive methods. The multi-language support successfully bridges the language gap for Hindi and Marathi speakers, making PDF comprehension significantly faster.

## 8.2 Screenshots
*(Insert screenshots of your application here in your Word document)*
- Figure 8.1: Landing Page
- Figure 8.2: Login/Signup Interface
- Figure 8.3: Dashboard & File Upload Interface
- Figure 8.4: Summarization Result Page (showing English and Translated versions)

---

# CHAPTER 9 APPLICATIONS
1. **Education:** Students can summarize lengthy research papers, textbooks, and notes.
2. **Corporate/Business:** Professionals can quickly extract key points from long reports, legal documents, or financial statements.
3. **Accessibility:** The multi-language and TTS features make content accessible to users who prefer regional languages or auditory learning.
4. **Legal & Medical Field:** Summarizing case files or patient histories for quick review.

---

# CHAPTER 10 FUTURE SCOPE
1. **More Languages:** Expanding translation and OCR support to other regional Indian languages (e.g., Tamil, Telugu, Bengali) and global languages.
2. **Domain-Specific Models:** Fine-tuning summarization models specifically for legal, medical, or financial documents to improve context accuracy.
3. **Export Options:** Adding functionality to export the generated summaries as PDF, DOCX, or direct integration with tools like Notion or Google Docs.
4. **Chat with PDF:** Implementing a Retrieval-Augmented Generation (RAG) system where users can ask questions directly about the uploaded PDF.

---

# CHAPTER 11 CONCLUSION
Brevity AI successfully addresses the challenge of information overload by providing a comprehensive, intelligent platform for document summarization. By combining advanced ML models, robust OCR capabilities, and seamless regional language translation, it offers a versatile tool for varied user bases. The integration of modern web technologies ensures a smooth, scalable, and user-friendly experience, demonstrating the practical application of AI in everyday productivity tools.

---

# CHAPTER 12 Appendix
## Appendix A: Problem statement feasibility
The problem statement was deemed highly feasible given the availability of open-source models (Hugging Face) and robust frameworks (React, FastAPI). The computational requirements were effectively managed via efficient backend processing and proper cloud deployment strategies.

## Appendix B: Details of paper publication
*(If your group published a paper based on this project, provide the details here: Title, Journal/Conference Name, Date, Authors. Otherwise, remove this section)*

## Appendix C: Plagiarism Report of the project
*(Insert screenshot or summary of Turnitin/Plagiarism checker report for your actual project documentation)*

---

# CHAPTER 13 References
1. Mihalcea, R., & Tarau, P. (2004). TextRank: Bringing Order into Texts. *Association for Computational Linguistics*.
2. Lewis, M., et al. (2019). BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation, Translation, and Comprehension. *arXiv preprint arXiv:1910.13461*.
3. Tiedemann, J., & Thottingal, S. (2020). OPUS-MT - Building open translation services for the World. *EAMT*.
4. FastAPI Documentation: https://fastapi.tiangolo.com/
5. React Documentation: https://reactjs.org/
6. Tesseract OCR Documentation: https://github.com/tesseract-ocr/tesseract
