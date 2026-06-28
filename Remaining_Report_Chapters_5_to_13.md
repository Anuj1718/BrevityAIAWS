# CHAPTER 5 PROJECT PLAN

## 5.1 Project Estimate
- **Development Time:** Approximately 3 to 4 months.
- **Cost:** The project utilizes predominantly open-source software and frameworks, keeping the software licensing cost to zero. Hosting costs for the deployment phase are minimal, utilizing AWS free-tier services, Render, or Vercel.

## 5.2 Risk Management
- **Risk 1: High Computational Resource Usage.** AI models, particularly abstractive summarization, demand high memory.
  **Mitigation:** Implemented LRU caching, chunked processing for large documents, and extractive fallbacks when memory limits are reached.
- **Risk 2: OCR Inaccuracies.** Low-quality scanned documents yield poor OCR results.
  **Mitigation:** Integrated image preprocessing techniques using OpenCV to enhance image quality before feeding it to the Tesseract OCR engine.
- **Risk 3: API Latency.** Lengthy processing times for large PDFs can lead to request timeouts.
  **Mitigation:** Adopted asynchronous processing with FastAPI to prevent blocking and ensure reliable communication between the client and server.

## 5.3 Project Schedule
1. **Month 1:** Requirement gathering, literature survey, UI/UX conceptualization, and basic frontend/backend setup.
2. **Month 2:** Integration of PyMuPDF for text extraction, implementation of extractive summarization (TextRank, TF-IDF), and setting up Firebase authentication.
3. **Month 3:** Implementation of Tesseract OCR for scanned PDFs, integration of BART for abstractive summarization, and incorporating translation models (Hindi and Marathi).
4. **Month 4:** Comprehensive system testing, UI refinement, deployment on cloud platforms (AWS, Vercel, Render), and final report documentation.

## 5.4 Team Organization
*(Please fill in your team member names and their specific responsibilities below)*
- **Team Member 1:** Frontend Development and UI/UX Design (React, Vite)
- **Team Member 2:** Backend API Architecture and Database Integration (FastAPI, Firebase)
- **Team Member 3:** Machine Learning Models and OCR Pipelines Integration (Hugging Face, Tesseract)

---

# CHAPTER 6 PROJECT IMPLEMENTATION

## 6.1 Overview of Project Modules
1. **Authentication Module:** Handles user registration, secure login, and session management using Firebase Authentication.
2. **Ingestion & Document Intelligence Module:** Manages the uploading of PDF files (up to 300MB), validates the file types, and automatically determines if the document requires standard text extraction or OCR.
3. **Extraction & Preprocessing Module:** Utilizes PyMuPDF to extract text from standard PDFs. For scanned documents, it applies OpenCV for image enhancement followed by Tesseract OCR. The extracted text is then normalized, and stopwords/special characters are handled via NLTK.
4. **Hybrid NLP Summarization Engine:**
   - *Extractive Summarization:* Uses scikit-learn and NLTK for approaches like TextRank, TF-IDF, and LSA.
   - *Abstractive Summarization:* Uses Hugging Face's `facebook/bart-large-cnn` model to generate context-aware summaries.
   - *Hybrid Approach:* Combines both methods to ensure factual accuracy and fluid readability.
5. **Multi-Modal Post-Processing Module (Translation & TTS):** Integrates translation models (Helsinki-NLP/opus-mt-en-hi and T5) to convert summaries into Hindi and Marathi. It also includes Text-to-Speech (TTS) functionality for audio output.

## 6.2 Tools and Technologies used
- **Frontend Presentation:** React 19, Vite 7, React Router 7, CSS Variables, Lottie & Spline for UI animations.
- **Backend & API Gateway:** Python 3.11+, FastAPI, Uvicorn.
- **Machine Learning & NLP:** PyTorch, Hugging Face Transformers, NLTK, scikit-learn.
- **Document Processing Utilities:** PyMuPDF, Tesseract OCR, OpenCV, PIL.
- **Database & Auth:** Firebase Firestore, Firebase Authentication.
- **Deployment & Hosting:** Vercel (Frontend CDN), Render/AWS EC2 (Backend Services).

## 6.3 Algorithm details
- **TextRank Algorithm:** An extractive, graph-based ranking model. Sentences are treated as vertices, and edges are formed based on word overlap or semantic similarity. The algorithm recursively computes the importance of each sentence, extracting the highest-ranked ones to form the summary.
- **BART (Bidirectional and Auto-Regressive Transformers):** Used for abstractive summarization. BART is a denoising autoencoder built on a standard sequence-to-sequence transformer architecture. It reads the source document bidirectionally to grasp the complete context and generates the summary auto-regressively, resulting in human-like phrasing.
- **TF-IDF (Term Frequency-Inverse Document Frequency):** Used for extractive summarization. It calculates the statistical importance of words in a document relative to a corpus, scoring sentences based on the weight of the words they contain.

---

# CHAPTER 7 SOFTWARE TESTING

## 7.1 Types of Testing
- **Unit Testing:** Individual components and utility functions (e.g., text cleaner, OCR processor) were tested in isolation to ensure correct output for a given input.
- **Integration Testing:** Verified that the frontend React application correctly communicates with the FastAPI backend, ensuring smooth data flow from file upload to summary retrieval.
- **Performance Testing:** Evaluated the system's ability to handle large PDF files (up to the 300MB limit). Testing confirmed that the chunked processing and thread pools effectively prevent server timeouts.
- **Usability Testing:** Conducted with sample users to ensure the UI is intuitive, the drag-and-drop features work seamlessly, and the translation options are easily accessible.

## 7.2 Test Case Result

| Test Case ID | Description | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| TC_01 | User Authentication via Firebase | User can successfully sign up and log in. | Registration and login succeed, session maintained. | Pass |
| TC_02 | Upload standard, searchable PDF | Text is extracted rapidly without invoking OCR. | PyMuPDF extracts text successfully and instantly. | Pass |
| TC_03 | Upload scanned/image-based PDF | System detects image PDF, activates OCR, and extracts text. | Tesseract OCR activates and extracts text with high accuracy. | Pass |
| TC_04 | Generate Abstractive Summary | The system returns a concise, context-aware summary. | BART model generates an accurate abstractive summary. | Pass |
| TC_05 | Translate Summary to Marathi/Hindi | The English summary is accurately translated into the chosen language. | Translation models return correct Hindi/Marathi text. | Pass |
| TC_06 | Exceed File Size Limit (> 300MB) | The system rejects the upload and displays an error. | Upload is blocked, and a size limit error is shown. | Pass |
| TC_07 | Text-to-Speech (TTS) Activation | The system generates audio playback of the summary text. | Audio plays clearly matching the summary content. | Pass |

---

# CHAPTER 8 RESULTS

## 8.1 Outcomes
The Brevity AI platform was successfully developed, integrated, and deployed. The system accurately differentiates between standard and scanned documents, applying robust OCR processing only when necessary. It successfully generates coherent summaries using both extractive and abstractive methodologies. The integration of multi-language support (Hindi and Marathi) and TTS features significantly enhances accessibility. The application demonstrates high stability, even when processing complex PDFs, thanks to its optimized asynchronous backend architecture.

## 8.2 Screenshots
*(Insert screenshots of your application here in your Word document)*
- **Figure 8.1:** Home / Landing Page
- **Figure 8.2:** User Login and Authentication Interface
- **Figure 8.3:** Dashboard and File Upload Interface
- **Figure 8.4:** Summarization Result Page (Displaying the original summary, translated summary, and TTS controls)

---

# CHAPTER 9 APPLICATIONS
1. **Academic and Research:** Students and researchers can rapidly condense lengthy academic papers, journals, and textbooks to grasp core concepts efficiently.
2. **Corporate and Legal:** Professionals can extract critical points from extensive financial reports, meeting minutes, and legal contracts, saving significant reading time.
3. **Accessibility:** The built-in Text-to-Speech (TTS) and regional language translation features make digital content highly accessible to visually impaired users or those who are more comfortable with Hindi or Marathi.
4. **Media and Content Curation:** Journalists and content creators can summarize long articles and reports to create brief news digests.

---

# CHAPTER 10 FUTURE SCOPE
1. **Expanded Linguistic Support:** Extending translation, OCR, and TTS capabilities to encompass a broader range of regional Indian languages (e.g., Tamil, Telugu, Bengali) and international languages.
2. **Domain-Specific Fine-Tuning:** Training and fine-tuning the summarization models specifically on legal, medical, or technical datasets to improve contextual accuracy in specialized fields.
3. **Interactive PDF Chat (RAG):** Implementing a Retrieval-Augmented Generation (RAG) feature, allowing users to interactively query and "chat" with the uploaded document to find specific answers.
4. **Advanced Export Options:** Adding capabilities to export the generated summaries and translations directly into formats like DOCX, PDF, or integrating with productivity tools like Notion and Google Workspace.

---

# CHAPTER 11 CONCLUSION
Brevity AI successfully mitigates the widespread issue of information overload by providing an intelligent, full-stack platform for document summarization. By amalgamating advanced machine learning models, robust OCR capabilities, and seamless regional language translation, it serves as a highly versatile tool for a diverse user base. The project demonstrates the practical and impactful application of Natural Language Processing and modern web technologies, resulting in a scalable, user-friendly, and highly accessible digital solution.

---

# CHAPTER 12 Appendix

## Appendix A: Problem statement feasibility
The chosen problem statement was highly feasible due to the availability of powerful open-source AI models (Hugging Face) and robust development frameworks (React, FastAPI). The computational demands of NLP models were successfully managed through efficient backend processing, caching strategies, and strategic cloud deployment.

## Appendix B: Details of paper publication
*(If your group published a research paper based on this project, provide the details here: Title, Journal/Conference Name, Date, Authors. If not, you may remove this section.)*

## Appendix C: Plagiarism Report of the project
*(Insert a screenshot or summary of the Turnitin/Plagiarism checker report for your actual project documentation here.)*

---

# CHAPTER 13 References
1. Mihalcea, R., & Tarau, P. (2004). TextRank: Bringing Order into Texts. *Proceedings of the 2004 Conference on Empirical Methods in Natural Language Processing*.
2. Lewis, M., et al. (2019). BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation, Translation, and Comprehension. *arXiv preprint arXiv:1910.13461*.
3. Tiedemann, J., & Thottingal, S. (2020). OPUS-MT - Building open translation services for the World. *Proceedings of the 22nd Annual Conference of the European Association for Machine Translation*.
4. FastAPI Documentation: https://fastapi.tiangolo.com/
5. React Documentation: https://reactjs.org/
6. Tesseract OCR Documentation: https://tesseract-ocr.github.io/
7. Hugging Face Transformers: https://huggingface.co/docs/transformers/
