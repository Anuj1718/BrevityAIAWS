import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import './Upload.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const FREE_TIER_MODE = (import.meta.env.VITE_FREE_TIER_MODE || 'true').toLowerCase() === 'true';

export default function Upload() {
  const [files, setFiles] = useState([]);
  const [backendFilename, setBackendFilename] = useState('');
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [summaryData, setSummaryData] = useState(null);
  const [activeSummary, setActiveSummary] = useState('');
  const [summaryButtonsEnabled, setSummaryButtonsEnabled] = useState(false);
  const [translatedSummary, setTranslatedSummary] = useState(null);
  const [isTranslating, setIsTranslating] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentUtterance, setCurrentUtterance] = useState(null);
  
  // Enhanced settings state
  const [settings, setSettings] = useState({
    useOcr: false,
    ocrQuality: 'medium',
    preprocessImages: true,
    ocrLanguages: 'eng+hin+mar',
    summaryType: FREE_TIER_MODE ? 'extractive' : 'abstractive',
    maxLength: FREE_TIER_MODE ? 150 : 200,
    minLength: FREE_TIER_MODE ? 30 : 50,
    extractiveRatio: FREE_TIER_MODE ? 0.35 : 0.5,
    useCache: true,
    usePipeline: !FREE_TIER_MODE
  });

  const [processingStep, setProcessingStep] = useState('');
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback((acceptedFiles, rejections) => {
    setError('');
    setSummaryData(null);
    setTranslatedSummary(null);
    setBackendFilename('');
    setSummaryButtonsEnabled(false);
    setProcessingStep('');
    setProgress(0);
    
    if (rejections?.length) {
      setError('Only PDFs are allowed and must be within size limits.');
      return;
    }
    const pdfs = acceptedFiles.filter((f) => f.type === 'application/pdf');
    if (!pdfs.length) return setError('Please drop PDF files (.pdf).');
    setFiles(pdfs);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: false,
    maxSize: 300 * 1024 * 1024,
  });

  function clearAll() {
    setFiles([]);
    setSummaryData(null);
    setTranslatedSummary(null);
    setBackendFilename('');
    setSummaryButtonsEnabled(false);
    setError('');
    setProcessingStep('');
    setProgress(0);
  }

  function updateSettings(newSettings) {
    setSettings(prev => ({ ...prev, ...newSettings }));
  }

  // Text-to-Speech functionality using Google Translate TTS for Hindi/Marathi
  function speakText(text, language = 'en-US') {
    // Stop any current speech
    if (currentUtterance) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
      setCurrentUtterance(null);
    }

    if (!text) {
      alert('No text available to read aloud.');
      return;
    }

    // For Hindi and Marathi, use Google Translate TTS (more reliable)
    if (language === 'hi-IN' || language === 'mr-IN') {
      playGoogleTTS(text, language);
      return;
    }

    // Check if speech synthesis is supported
    if (!window.speechSynthesis) {
      alert('Text-to-speech is not supported in this browser.');
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    
    // Configure voice settings
    utterance.lang = language;
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Helper function to find voice
    const findAndSpeak = () => {
      const voices = window.speechSynthesis.getVoices();
      
      const preferredVoices = {
        'en-US': ['Microsoft Zira', 'Google US English', 'Samantha', 'Alex'],
        'en-GB': ['Google UK English', 'Microsoft Hazel']
      };

      const preferred = preferredVoices[language] || preferredVoices['en-US'];

      let selectedVoice = voices.find(voice => 
        preferred.some(pref => voice.name.toLowerCase().includes(pref.toLowerCase()))
      );

      if (!selectedVoice) {
        selectedVoice = voices.find(voice => 
          voice.lang.toLowerCase().startsWith(language.split('-')[0].toLowerCase())
        );
      }

      if (!selectedVoice && voices.length > 0) {
        selectedVoice = voices[0];
      }

      if (selectedVoice) {
        utterance.voice = selectedVoice;
      }

      return selectedVoice;
    };

    utterance.onstart = () => {
      setIsPlaying(true);
      setCurrentUtterance(utterance);
    };

    utterance.onend = () => {
      setIsPlaying(false);
      setCurrentUtterance(null);
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      setIsPlaying(false);
      setCurrentUtterance(null);
      if (event.error !== 'interrupted' && event.error !== 'canceled') {
        alert(`Text-to-speech error. Please try again.`);
      }
    };

    const voices = window.speechSynthesis.getVoices();
    if (voices.length === 0) {
      window.speechSynthesis.onvoiceschanged = () => {
        findAndSpeak();
        window.speechSynthesis.speak(utterance);
      };
    } else {
      findAndSpeak();
      window.speechSynthesis.speak(utterance);
    }
  }

  // Google Translate TTS for Hindi/Marathi (more reliable than browser TTS)
  function playGoogleTTS(text, language) {
    const langCode = language === 'hi-IN' ? 'hi' : 'mr';
    
    // Split text into chunks (Google TTS has ~200 char limit per request)
    const maxChunkLength = 180;
    const chunks = [];
    let remainingText = text;
    
    while (remainingText.length > 0) {
      if (remainingText.length <= maxChunkLength) {
        chunks.push(remainingText);
        break;
      }
      
      // Find a good break point (period, comma, or space)
      let breakPoint = remainingText.lastIndexOf('।', maxChunkLength); // Hindi/Marathi full stop
      if (breakPoint === -1) breakPoint = remainingText.lastIndexOf('.', maxChunkLength);
      if (breakPoint === -1) breakPoint = remainingText.lastIndexOf(',', maxChunkLength);
      if (breakPoint === -1) breakPoint = remainingText.lastIndexOf(' ', maxChunkLength);
      if (breakPoint === -1) breakPoint = maxChunkLength;
      
      chunks.push(remainingText.substring(0, breakPoint + 1).trim());
      remainingText = remainingText.substring(breakPoint + 1).trim();
    }

    setIsPlaying(true);
    let currentChunkIndex = 0;
    let currentAudio = null;

    const playNextChunk = () => {
      if (currentChunkIndex >= chunks.length) {
        setIsPlaying(false);
        setCurrentUtterance(null);
        return;
      }

      const chunk = chunks[currentChunkIndex];
      const encodedText = encodeURIComponent(chunk);
      const audioUrl = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encodedText}&tl=${langCode}&client=tw-ob`;

      currentAudio = new Audio(audioUrl);
      currentAudio.playbackRate = 0.9; // Slightly slower for clarity
      
      currentAudio.onended = () => {
        currentChunkIndex++;
        playNextChunk();
      };

      currentAudio.onerror = (e) => {
        console.error('Google TTS error:', e);
        // Fallback to browser TTS if Google TTS fails
        fallbackToBrowserTTS(text, language);
      };

      currentAudio.play().catch(err => {
        console.error('Audio play error:', err);
        fallbackToBrowserTTS(text, language);
      });

      // Store reference for stopping
      setCurrentUtterance({ audio: currentAudio, stop: () => {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentChunkIndex = chunks.length; // Stop playing more chunks
      }});
    };

    playNextChunk();
  }

  // Fallback to browser TTS if Google TTS fails
  function fallbackToBrowserTTS(text, language) {
    if (!window.speechSynthesis) {
      alert('Text-to-speech is not available. Please try a different browser.');
      setIsPlaying(false);
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language;
    utterance.rate = 0.8;

    const voices = window.speechSynthesis.getVoices();
    const langCode = language.split('-')[0];
    const matchingVoice = voices.find(v => v.lang.startsWith(langCode));
    
    if (matchingVoice) {
      utterance.voice = matchingVoice;
    } else {
      alert(`No voice available for ${language === 'hi-IN' ? 'Hindi' : 'Marathi'}. Your browser may not support this language.`);
      setIsPlaying(false);
      return;
    }

    utterance.onend = () => {
      setIsPlaying(false);
      setCurrentUtterance(null);
    };

    utterance.onerror = () => {
      setIsPlaying(false);
      setCurrentUtterance(null);
    };

    window.speechSynthesis.speak(utterance);
    setCurrentUtterance(utterance);
  }

  function stopSpeech() {
    // Stop Google TTS audio if playing
    if (currentUtterance && currentUtterance.audio) {
      currentUtterance.stop();
    }
    // Stop browser TTS
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsPlaying(false);
    setCurrentUtterance(null);
  }

  function getSummaryText() {
    if (!summaryData) return '';

    if (activeSummary === 'formatted-hybrid') {
      let text = '';
      if (summaryData.title) text += `Title: ${summaryData.title}. `;
      if (summaryData.objective) text += `Objective: ${summaryData.objective}. `;
      if (summaryData.key_points && Array.isArray(summaryData.key_points)) {
        text += `Key Points: ${summaryData.key_points.join('. ')}. `;
      }
      if (summaryData.final_abstract) text += `Final Abstract: ${summaryData.final_abstract}.`;
      return text;
    } else if (activeSummary === 'extractive' || activeSummary === 'abstractive') {
      return summaryData.summary_text || '';
    }
    return '';
  }

  function getTranslatedText() {
    if (!translatedSummary) return '';
    return translatedSummary.translated_summary || '';
  }

  async function detectTextType(filename) {
    try {
      const encodedFilename = encodeURIComponent(filename.replace(/\\/g, '/'));
      const resp = await fetch(`${API_BASE}/api/extract/detect-text-type/${encodedFilename}`);
      const data = await resp.json();
      return data;
    } catch (error) {
      console.error('Text type detection failed:', error);
      return null;
    }
  }

  function exportToPDF() {
    if (!summaryData) {
      alert('No summary data available. Please generate a summary first.');
      return;
    }

    const now = new Date();
    const summaryType = activeSummary === 'formatted-hybrid' ? 'Formatted Hybrid Summary' : 
                       activeSummary === 'extractive' ? 'Extractive Summary' : 'Abstractive Summary';
    
    // Create HTML content for browser print
    let htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Document Summary Report</title>
        <style>
          @page {
            margin: 0.5in;
            size: A4;
          }
          body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
            color: #333;
            font-size: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
          }
          .container {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
          }
          .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
          }
          .title {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
          }
          .metadata {
            font-size: 11px;
            color: #666;
            margin-bottom: 20px;
          }
          .section {
            margin-bottom: 25px;
            page-break-inside: avoid;
            background: #f8f9ff;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
          }
          .section-title {
            font-size: 16px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
          }
          .content {
            margin-left: 10px;
            margin-bottom: 10px;
            text-align: justify;
          }
          .key-points {
            margin-left: 10px;
          }
          .key-points li {
            margin-bottom: 6px;
            padding-left: 5px;
          }
          .footer {
            margin-top: 30px;
            text-align: center;
            font-size: 9px;
            color: #666;
            border-top: 2px solid #667eea;
            padding-top: 15px;
          }
          .stats {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            padding: 15px;
            background: #f0f4ff;
            border-radius: 8px;
          }
          .stat-item {
            text-align: center;
          }
          .stat-value {
            font-size: 18px;
            font-weight: bold;
            color: #667eea;
          }
          .stat-label {
            font-size: 10px;
            color: #666;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <div class="title">📄 Document Summary Report</div>
            <div class="metadata">
              Generated on: ${now.toLocaleDateString()} at ${now.toLocaleTimeString()}<br>
              ${backendFilename ? `Source File: ${backendFilename}<br>` : ''}
              Summary Type: ${summaryType}<br>
              ${settings.useOcr ? `OCR Quality: ${settings.ocrQuality} | Languages: ${settings.ocrLanguages}` : 'Direct Text Extraction'}
            </div>
          </div>
    `;

    // Add processing stats if available
    if (summaryData.original_length || summaryData.summary_length) {
      htmlContent += `
        <div class="stats">
          <div class="stat-item">
            <div class="stat-value">${summaryData.original_length || 'N/A'}</div>
            <div class="stat-label">Original Words</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">${summaryData.summary_length || 'N/A'}</div>
            <div class="stat-label">Summary Words</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">${summaryData.compression_ratio ? (summaryData.compression_ratio * 100).toFixed(1) + '%' : 'N/A'}</div>
            <div class="stat-label">Compression</div>
          </div>
        </div>
      `;
    }

    if (activeSummary === 'formatted-hybrid') {
      if (summaryData.title) {
        htmlContent += `<div class="section"><div class="section-title">📋 Title</div><div class="content">${summaryData.title}</div></div>`;
      }
      
      if (summaryData.objective) {
        htmlContent += `<div class="section"><div class="section-title">🎯 Objective</div><div class="content">${summaryData.objective}</div></div>`;
      }
      
      if (summaryData.key_points && Array.isArray(summaryData.key_points)) {
        htmlContent += `<div class="section"><div class="section-title">✨ Key Points</div><ul class="key-points">`;
        summaryData.key_points.forEach(point => {
          htmlContent += `<li>${point}</li>`;
        });
        htmlContent += `</ul></div>`;
      }
      
      if (summaryData.final_abstract) {
        htmlContent += `<div class="section"><div class="section-title">📝 Final Abstract</div><div class="content">${summaryData.final_abstract}</div></div>`;
      }
    } else if (activeSummary === 'extractive') {
      if (summaryData.summary_text) {
        htmlContent += `<div class="section"><div class="section-title">📊 Extractive Summary</div><div class="content">${summaryData.summary_text}</div></div>`;
      }
    } else if (activeSummary === 'abstractive') {
      if (summaryData.summary_text) {
        htmlContent += `<div class="section"><div class="section-title">🧠 Abstractive Summary</div><div class="content">${summaryData.summary_text}</div></div>`;
      }
    }

    htmlContent += `
          <div class="footer">
            Generated by Brevity - Advanced Document Summarization Tool<br>
            ©2025 SummarizePDF. All rights reserved.
          </div>
        </div>
      </body>
      </html>
    `;

    // Create a new window with the content
    const newWindow = window.open('', '_blank');
    newWindow.document.write(htmlContent);
    newWindow.document.close();
    
    // Wait for content to load, then trigger print
    newWindow.onload = function() {
      newWindow.print();
      setTimeout(() => {
        newWindow.close();
      }, 1000);
    };
  }

  async function safeJson(resp) {
    try {
      return await resp.json();
    } catch {
      return null;
    }
  }

  async function startUpload() {
    setError('');
    setSummaryData(null);
    setTranslatedSummary(null);
    setActiveSummary('');
    setSummaryButtonsEnabled(false);
    setProcessingStep('');
    setProgress(0);

    if (!files.length) {
      setError('Pick a PDF first.');
      return;
    }

    setUploading(true);
    const originalName = files[0].name;

    try {
      // Step 1: Upload file with progress tracking
      setProcessingStep('Uploading file...');
      setProgress(0);
      
      const formData = new FormData();
      formData.append('file', files[0]);

      // Use XMLHttpRequest for upload progress tracking
      const uploadJson = await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        // Track upload progress
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            setProgress(Math.min(percentComplete * 0.3, 30)); // Scale to 0-30%
            setProcessingStep(`Uploading file... ${percentComplete}%`);
          }
        });
        
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              resolve(JSON.parse(xhr.responseText));
            } catch {
              resolve(null);
            }
          } else {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        });
        
        xhr.addEventListener('error', () => {
          reject(new Error('Upload failed due to network error'));
        });
        
        xhr.open('POST', `${API_BASE}/api/upload/pdf`);
        xhr.send(formData);
      });

      console.log('UPLOAD RESPONSE:', uploadJson);

      let filename = null;
      if (uploadJson) {
        if (uploadJson.filename) filename = uploadJson.filename;
        else if (Array.isArray(uploadJson.files) && uploadJson.files.length) filename = uploadJson.files[0].filename;
        else if (uploadJson.file_path) {
          const p = uploadJson.file_path.replace(/\\/g, '/').split('/');
          filename = p[p.length - 1];
        }
      }

      if (!filename) {
        const listResp = await fetch(`${API_BASE}/api/upload/files`);
        const listJson = await safeJson(listResp);
        console.log('UPLOAD FILES LIST:', listResp.status, listJson);
        if (listJson?.files?.length) {
          const found = [...listJson.files].reverse().find(f =>
            (f.filename && f.filename.endsWith(originalName)) ||
            (f.file_path && f.file_path.replace(/\\/g, '/').endsWith(originalName)) ||
            (f.filename && f.filename.includes(originalName))
          );
          if (found) filename = found.filename;
        }
      }

      if (!filename) {
        const debug = uploadJson ? JSON.stringify(uploadJson) : 'No response data';
        throw new Error(`Upload did not return backend filename. Debug: ${debug}`);
      }

      console.log('Using backend filename:', filename);
      setBackendFilename(filename);

      // Step 2: Detect text type and suggest OCR if needed
      setProcessingStep('Analyzing document...');
      setProgress(35);
      
      const textTypeInfo = await detectTextType(filename);
      if (textTypeInfo && textTypeInfo.text_type === 'scanned' && !settings.useOcr) {
        // Suggest OCR for scanned documents
        const useOcr = confirm(`This appears to be a scanned document. Would you like to enable OCR for better text extraction?`);
        updateSettings({ useOcr });
      }

      const encodedFilename = encodeURIComponent(filename.replace(/\\/g, '/'));

      // Step 3: Extract text
      setProcessingStep('Extracting text...');
      setProgress(55);
      
      const extractParams = new URLSearchParams({
        use_ocr: settings.useOcr,
        lang: settings.ocrLanguages,
        chunk_size: 50,
        ocr_quality: settings.ocrQuality,
        preprocess_images: settings.preprocessImages
      });
      
      const extractURL = `${API_BASE}/api/extract/text/${encodedFilename}?${extractParams}`;
      const extractResp = await fetch(extractURL, { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: '{}' 
      });
      const extractJson = await safeJson(extractResp);
      console.log('EXTRACT RESP:', extractResp.status, extractJson);
      if (!extractResp.ok) {
        const msg = (extractJson && (extractJson.detail || extractJson.message)) || `status ${extractResp.status}`;
        throw new Error(`Extraction failed: ${msg}`);
      }

      // Step 4: Clean text
      setProcessingStep('Cleaning text...');
      setProgress(75);
      
      const cleanURL = `${API_BASE}/api/clean/text/${encodedFilename}?remove_stopwords=true&normalize_whitespace=true&remove_special_chars=true&min_sentence_length=15`;
      const cleanResp = await fetch(cleanURL, { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: '{}' 
      });
      const cleanJson = await safeJson(cleanResp);
      console.log('CLEAN RESP:', cleanResp.status, cleanJson);
      if (!cleanResp.ok) {
        const msg = (cleanJson && (cleanJson.detail || cleanJson.message)) || `status ${cleanResp.status}`;
        throw new Error(`Cleaning failed: ${msg}`);
      }

      setProcessingStep('Ready for summarization!');
      setProgress(100);
      setSummaryButtonsEnabled(true);
      
      setTimeout(() => {
        setProcessingStep('');
        setProgress(0);
      }, 2000);
      
    } catch (err) {
      console.error('PROCESS ERROR:', err);
      setError(err.message || 'Something went wrong during upload/processing.');
      setProcessingStep('');
      setProgress(0);
    } finally {
      setUploading(false);
    }
  }

  async function fetchSummary(type) {
    setError('');
    setSummaryData(null);
    setTranslatedSummary(null);
    setActiveSummary(type);

    let filenameToUse = backendFilename;
    if (!filenameToUse && files[0]) filenameToUse = files[0].name;
    if (!filenameToUse) {
      setError('No filename available. Upload file first.');
      return;
    }

    setUploading(true);
    setProcessingStep(`Generating ${type} summary...`);
    setProgress(0);

    try {
      const encodedFilename = encodeURIComponent(filenameToUse.replace(/\\/g, '/'));

      let url = '';
      let query = '';

      if (type === 'extractive') {
        url = `${API_BASE}/api/summarize/extractive/${encodedFilename}`;
        query = new URLSearchParams({ 
          use_cache: settings.useCache,
          summary_ratio: String(settings.extractiveRatio),
          algorithm: 'textrank'
        }).toString();
      } else if (type === 'abstractive') {
        url = `${API_BASE}/api/summarize/abstractive/${encodedFilename}`;
        query = new URLSearchParams({ 
          max_length: settings.maxLength, 
          min_length: settings.minLength,
          use_pipeline: settings.usePipeline
        }).toString();
      } else if (type === 'formatted-hybrid' || type === 'hybrid') {
        url = `${API_BASE}/api/summarize/formatted-hybrid/${encodedFilename}`;
        query = new URLSearchParams({ 
          extractive_ratio: settings.extractiveRatio, 
          max_length: settings.maxLength, 
          min_length: settings.minLength,
          use_cache: settings.useCache,
          use_pipeline: settings.usePipeline
        }).toString();
      } else {
        throw new Error('Unknown summary type');
      }

      const fullUrl = query ? `${url}?${query}` : url;
      console.log('SUMMARY REQUEST:', fullUrl);

      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 500);

      const resp = await fetch(fullUrl, { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: '{}' 
      });
      const json = await safeJson(resp);
      console.log('SUMMARY RESP:', resp.status, json);

      clearInterval(progressInterval);
      setProgress(100);

      if (!resp.ok) {
        const msg = (json && (json.detail || json.message)) || `status ${resp.status}`;
        throw new Error(`Summary generation failed: ${msg}`);
      }

      if (json?.fallback_used) {
        setActiveSummary('extractive');
      }

      setSummaryData(json);
      setProcessingStep('Summary generated successfully!');
      
      setTimeout(() => {
        setProcessingStep('');
        setProgress(0);
      }, 2000);
      
    } catch (err) {
      console.error('SUMMARY ERROR:', err);
      setError(err.message || 'Something went wrong while fetching summary.');
      setProcessingStep('');
      setProgress(0);
    } finally {
      setUploading(false);
    }
  }

  async function translateSummary(targetLang = 'hindi') {
    if (!summaryData) {
      setError('No summary available to translate.');
      return;
    }

    setIsTranslating(true);
    setError('');

    try {
      const encodedFilename = encodeURIComponent(backendFilename.replace(/\\/g, '/'));
      const url = `${API_BASE}/api/translate/summary/${encodedFilename}?target_language=${targetLang}&summary_type=${activeSummary}`;
      
      const resp = await fetch(url, { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: '{}' 
      });
      const json = await safeJson(resp);
      
      console.log('Translation response:', json);

      if (!resp.ok) {
        throw new Error(json?.detail || json?.message || 'Translation failed');
      }

      setTranslatedSummary(json);
      
      // Show success message
      const langName = targetLang === 'hindi' ? 'Hindi' : 'Marathi';
      alert(`Translation to ${langName} completed successfully!`);
      
    } catch (err) {
      console.error('TRANSLATION ERROR:', err);
      setError(err.message || 'Translation failed');
    } finally {
      setIsTranslating(false);
    }
  }

  return (
    <div className="container section upload-hero">
      <div className="upload-grid">
        <div className="upload-copy stack">
          
          {!backendFilename && (
            <div>
              <h2 className="upload-title">PDF Summarization</h2>
              <p className="upload-sub">
                Upload your PDFs and get intelligent summaries with OCR support, 
                multiple summarization methods, and translation capabilities.
              </p>
            </div>
          )}
          
          {/* Enhanced Settings Panel */}
          {files.length > 0 && !summaryButtonsEnabled && (
            <div className="settings-panel">
              <h3 className="settings-title">⚙️ Processing Settings</h3>
              
              <div className="settings-grid">
                <div className="setting-group">
                  <label className="setting-label">
                    <input 
                      type="checkbox" 
                      checked={settings.useOcr}
                      onChange={(e) => updateSettings({ useOcr: e.target.checked })}
                    />
                    Enable OCR (for scanned PDFs)
                  </label>
                </div>

                {settings.useOcr && (
                  <>
                    <div className="setting-group">
                      <label className="setting-label">OCR Quality:</label>
                      <select 
                        value={settings.ocrQuality}
                        onChange={(e) => updateSettings({ ocrQuality: e.target.value })}
                        className="setting-select"
                      >
                        <option value="low">Low (Fast)</option>
                        <option value="medium">Medium (Balanced)</option>
                        <option value="high">High (Best Quality)</option>
                      </select>
                    </div>

                    <div className="setting-group">
                      <label className="setting-label">Languages:</label>
                      <select 
                        value={settings.ocrLanguages}
                        onChange={(e) => updateSettings({ ocrLanguages: e.target.value })}
                        className="setting-select"
                      >
                        <option value="eng">English Only</option>
                        <option value="hin">Hindi Only</option>
                        <option value="mar">Marathi Only</option>
                        <option value="eng+hin">English + Hindi</option>
                        <option value="eng+mar">English + Marathi</option>
                        <option value="eng+hin+mar">English + Hindi + Marathi</option>
                      </select>
                    </div>

                    <div className="setting-group">
                      <label className="setting-label">
                        <input 
                          type="checkbox" 
                          checked={settings.preprocessImages}
                          onChange={(e) => updateSettings({ preprocessImages: e.target.checked })}
                        />
                        Preprocess Images (Better OCR)
                      </label>
                    </div>
                  </>
                )}

                <div className="setting-group">
                  <label className="setting-label">Summary Type:</label>
                  <select 
                    value={settings.summaryType}
                    onChange={(e) => updateSettings({ summaryType: e.target.value })}
                    className="setting-select"
                  >
                    <option value="extractive">Extractive (Fastest for free tier)</option>
                    <option value="abstractive">Abstractive (AI-generated)</option>
                    <option value="formatted-hybrid">Formatted Hybrid (Structured)</option>
                  </select>
                </div>

                <div className="setting-group">
                  <label className="setting-label">Max Length: {settings.maxLength} words</label>
                  <input 
                    type="range" 
                    min="50" 
                    max="500" 
                    value={settings.maxLength}
                    onChange={(e) => updateSettings({ maxLength: parseInt(e.target.value) })}
                    className="setting-range"
                  />
                </div>

                <div className="setting-group">
                  <label className="setting-label">Min Length: {settings.minLength} words</label>
                  <input 
                    type="range" 
                    min="10" 
                    max="100" 
                    value={settings.minLength}
                    onChange={(e) => updateSettings({ minLength: parseInt(e.target.value) })}
                    className="setting-range"
                  />
                </div>

                <div className="setting-group">
                  <label className="setting-label">
                    <input 
                      type="checkbox" 
                      checked={settings.useCache}
                      onChange={(e) => updateSettings({ useCache: e.target.checked })}
                    />
                    Use Cache (Faster processing)
                  </label>
                </div>

                <div className="setting-group">
                  <label className="setting-label">
                    <input 
                      type="checkbox" 
                      checked={settings.usePipeline}
                      onChange={(e) => updateSettings({ usePipeline: e.target.checked })}
                    />
                    Use Pipeline (Optimized processing)
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Progress Indicator */}
          {uploading && processingStep && (
            <div className="progress-panel">
              <div className="progress-header">
                <h4>{processingStep}</h4>
                <span className="progress-percent">{progress}%</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}
          
          {/* Enhanced Output Display */}
          {summaryData && (
            <div className="output-display" style={{ marginTop: 9 }}>
              {activeSummary === 'formatted-hybrid' && (
                <div className="summary-card hybrid">
                  <div className="summary-header">
                    <h3 className="summary-title">📋 {summaryData.title}</h3>
                    <div className="summary-stats">
                      <span className="stat">📊 {summaryData.original_length} → {summaryData.summary_length} words</span>
                      <span className="stat">📉 {summaryData.compression_ratio ? (summaryData.compression_ratio * 100).toFixed(1) + '%' : 'N/A'} compression</span>
                    </div>
                  </div>
                  
                  {summaryData.objective && (
                    <div className="summary-section">
                      <h4 className="section-title">🎯 Objective</h4>
                      <p className="section-content">{summaryData.objective}</p>
                    </div>
                  )}
                  
                  {summaryData.key_points && Array.isArray(summaryData.key_points) && (
                    <div className="summary-section">
                      <h4 className="section-title">✨ Key Points</h4>
                      <ul className="keypoints-list">
                        {summaryData.key_points.map((kp, i) => (
                          <li key={i}>• {kp}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {summaryData.final_abstract && (
                    <div className="summary-section">
                      <h4 className="section-title">📝 Final Abstract</h4>
                      <p className="section-content">{summaryData.final_abstract}</p>
                    </div>
                  )}
                </div>
              )}

              {activeSummary === 'extractive' && (
                <div className="summary-card extractive">
                  <div className="summary-header">
                    <h3 className="summary-title">📊 Extractive Summary</h3>
                    <div className="summary-stats">
                      <span className="stat">📊 {summaryData.original_length} → {summaryData.summary_length} words</span>
                      <span className="stat">📉 {summaryData.compression_ratio ? (summaryData.compression_ratio * 100).toFixed(1) + '%' : 'N/A'} compression</span>
                    </div>
                  </div>
                  <p className="abstract-text">{summaryData.summary_text}</p>
                </div>
              )}

              {activeSummary === 'abstractive' && (
                <div className="summary-card abstractive">
                  <div className="summary-header">
                    <h3 className="summary-title">🧠 Abstractive Summary</h3>
                    <div className="summary-stats">
                      <span className="stat">📊 {summaryData.original_length} → {summaryData.summary_length} words</span>
                      <span className="stat">📉 {summaryData.compression_ratio ? (summaryData.compression_ratio * 100).toFixed(1) + '%' : 'N/A'} compression</span>
                      <span className="stat">🤖 {summaryData.model || 'BART'}</span>
                    </div>
                  </div>
                  <p className="abstract-text">{summaryData.summary_text}</p>
                </div>
              )}

              {/* Translation Section */}
              {summaryData && (
                <div className="translation-section">
                  <h4 className="section-title">🌐 Translation</h4>
                  <div className="translation-buttons">
                    <button 
                      className="btn outline translation-btn"
                      onClick={() => translateSummary('hindi')}
                      disabled={isTranslating}
                    >
                      {isTranslating ? 'Translating...' : '🇮🇳 Translate to Hindi'}
                    </button>
                    <button 
                      className="btn outline translation-btn"
                      onClick={() => translateSummary('marathi')}
                      disabled={isTranslating}
                    >
                      {isTranslating ? 'Translating...' : '🇮🇳 Translate to Marathi'}
                    </button>
                  </div>
                  
                  {translatedSummary && (
                    <div className="translated-content">
                      <div className="translated-header">
                        <h5>Translated Summary ({translatedSummary.target_language === 'hindi' ? 'Hindi' : 'Marathi'}):</h5>
                        <button 
                          className={`btn outline audio-btn-small ${isPlaying ? 'playing' : ''}`}
                          onClick={() => {
                            if (isPlaying) {
                              stopSpeech();
                            } else {
                              const textToSpeak = getTranslatedText();
                              const language = translatedSummary.target_language === 'hindi' ? 'hi-IN' : 'mr-IN';
                              speakText(textToSpeak, language);
                            }
                          }}
                        >
                          {isPlaying ? '⏸️' : '🔊'}
                        </button>
                      </div>
                      <p className="translated-text">{translatedSummary.translated_summary}</p>
                    </div>
                  )}
                </div>
              )}
              
              {/* Enhanced Export Actions */}
              <div className="export-actions" style={{ marginTop: 16 }}>
                <button className="btn outline export-pdf-btn" onClick={exportToPDF}>
                  📄 Save as PDF
                </button>
                <button 
                  className="btn outline copy-btn"
                  onClick={() => {
                    const textToCopy = summaryData.summary_text || 
                      `${summaryData.title}\n\n${summaryData.objective}\n\nKey Points:\n${summaryData.key_points?.join('\n')}\n\n${summaryData.final_abstract}`;
                    navigator.clipboard.writeText(textToCopy);
                    alert('Summary copied to clipboard!');
                  }}
                >
                  📋 Copy Summary
                </button>
                <button 
                  className={`btn outline audio-btn ${isPlaying ? 'playing' : ''}`}
                  onClick={() => {
                    if (isPlaying) {
                      stopSpeech();
                    } else {
                      const textToSpeak = getSummaryText();
                      speakText(textToSpeak, 'en-US');
                    }
                  }}
                >
                  {isPlaying ? '⏸️ Stop Audio' : '🔊 Listen to Summary'}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="panel">
          <div {...getRootProps()} className={`dz ${isDragActive ? 'active' : ''} ${uploading ? 'disabled' : ''}`}>
            <input {...getInputProps()} />
            <div className="dz-illustration">📄</div>
            <div className="dz-title">Drag & drop PDFs here</div>
            <div className="dz-caption">or click to choose files</div>
            <button type="button" className="btn primary" style={{ marginTop: 12 }}>Browse files</button>
          </div>

          {error && <div className="dz-error" style={{ marginTop: 12 }}>{error}</div>}

          {files.length > 0 && (
            <>
              <ul className="file-list">
                {files.map((f, i) => (
                  <li key={i} className="file-item">
                    <div className="file-info">
                      <span className="file-name">{f.name}</span>
                      <span className="file-size">{(f.size / (1024 * 1024)).toFixed(1)} MB</span>
                    </div>
                  </li>
                ))}
              </ul>

              <div className="file-actions" style={{ marginTop: 10 }}>
                <button className="btn outline" onClick={clearAll} disabled={uploading}>Clear</button>
                <button className="btn primary" onClick={startUpload} disabled={uploading}>
                  {uploading ? 'Processing…' : 'Upload & Process'}
                </button>
              </div>
            </>
          )}

          {summaryButtonsEnabled && (
            <div className="summary-buttons" style={{ marginTop: 16 }}>
              <h4 className="summary-buttons-title">Choose Summary Type:</h4>
              <div className="summary-buttons-grid">
                <button 
                  className="btn outline summary-btn" 
                  onClick={() => fetchSummary('extractive')} 
                  disabled={uploading}
                >
                  📊 Extractive
                </button>
                <button 
                  className="btn outline summary-btn" 
                  onClick={() => fetchSummary('abstractive')} 
                  disabled={uploading}
                >
                  🧠 Abstractive
                </button>
                <button 
                  className="btn outline summary-btn" 
                  onClick={() => fetchSummary('formatted-hybrid')} 
                  disabled={uploading}
                >
                  📋 Formatted Hybrid
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}