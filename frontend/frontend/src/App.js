import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [originalImage, setOriginalImage] = useState(null);
  const [finalImage, setFinalImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [optimizeWithGA, setOptimizeWithGA] = useState(false);
  const [caricatureMode, setCaricatureMode] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState(0);
  const [darkMode, setDarkMode] = useState(false); // Default to light mode
  
  // Apply dark mode class to body
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [darkMode]);

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    processUploadedFile(file);
  };
  
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };
  
  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processUploadedFile(e.dataTransfer.files[0]);
    }
  };
  
  const processUploadedFile = (file) => {
    if (!file) return;
    
    setError(null);
    setFinalImage(null);
    
    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError("File size too large (max 10MB)");
      return;
    }
    
    // Check file type
    if (!file.type.match('image.*')) {
      setError("Please select an image file");
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      setOriginalImage(e.target.result);
    };
    reader.readAsDataURL(file);
  };
  
  const handleCartoonize = async () => {
    if (!originalImage) {
      setError("Please upload an image first");
      return;
    }
    
    setLoading(true);
    setError(null);
    setProgress(0);
    
    // Simulate progress intervals for better UX
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + Math.random() * 15;
        return newProgress >= 90 ? 90 : newProgress;
      });
    }, 500);
    
    try {
      // Create a FormData object to send the image
      const formData = new FormData();
      
      // Convert base64 string back to a file
      const base64Response = await fetch(originalImage);
      const blob = await base64Response.blob();
      const file = new File([blob], "input.jpg", { type: 'image/jpeg' });
      
      formData.append('image', file);
      formData.append('optimize', optimizeWithGA.toString());
      formData.append('caricature', caricatureMode.toString());
      
      console.log("Sending request to backend...");
      
      // Send the image to the Python backend
      const response = await fetch('http://127.0.0.1:5000/cartoonize', {
        method: 'POST',
        body: formData,
      });
      
      console.log("Response status:", response.status);
      
      if (!response.ok) {
        // Try to get error message from response
        let errorMessage = "Cartoonizing failed";
        try {
          const errorData = await response.json();
          if (errorData && errorData.error) {
            errorMessage = errorData.error;
          }
        } catch (e) {
          // If parsing failed, use the status text
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        
        throw new Error(errorMessage);
      }
      
      // Complete the progress bar
      setProgress(100);
      
      // Get the cartoonized image from the response
      const data = await response.json();
      console.log("Response received:", data);
      
      // Check if the response has the expected structure
      if (data.success && data.images) {
        // Only use the exaggerated image (final image)
        setFinalImage(data.images.exaggerated);
        console.log("Image processing successful!");
      } else {
        throw new Error('Invalid response format from server');
      }
    } catch (err) {
      console.error("Error during cartoonization:", err);
      setError("Failed to cartoonize image: " + err.message);
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
    }
  };
  
  return (
    <div className={`app-container ${darkMode ? 'dark-mode' : ''}`}>
      <header className="app-header">
        <div className="logo">
          <span className="logo-icon">🎨</span>
          <h1>Image Cartoonizer</h1>
        </div>
        <p>Transform your photos into amazing cartoon art using AI!</p>
        
        {/* Theme toggle button */}
        <button 
          className="theme-toggle" 
          onClick={() => setDarkMode(!darkMode)}
          aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
        >
          {darkMode ? '☀️' : '🌙'}
        </button>
      </header>
      
      <main className="main-content">
        <div 
          className={`upload-section ${dragActive ? 'drag-active' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          role="region"
          aria-label="Upload area"
        >
          <label className="upload-label">
            <input 
              type="file" 
              accept="image/*" 
              onChange={handleImageUpload} 
              aria-label="Upload image file" 
            />
            <div className="upload-button">
              <span className="upload-icon">📁</span>
              <span>Upload Image</span>
            </div>
          </label>
          <div className="upload-hint">or drag and drop your image here</div>
          
          <div className="options-container">
            <h3>Processing Options</h3>
            <div className="options">
              <label className="option-label" title="Uses genetic algorithms to find optimal cartoon parameters">
                <input
                  type="checkbox"
                  checked={optimizeWithGA}
                  onChange={(e) => setOptimizeWithGA(e.target.checked)}
                  aria-label="Optimize with Genetic Algorithm"
                />
                <span className="option-text">
                  <span className="option-icon">🧬</span>
                  Optimize with Genetic Algorithm
                </span>
                <span className="tooltip">Uses AI to find the best cartoon style for your image</span>
              </label>
              <label className="option-label" title="Creates a fun exaggerated version of your face">
                <input
                  type="checkbox"
                  checked={caricatureMode}
                  onChange={(e) => setCaricatureMode(e.target.checked)}
                  aria-label="Fun Semi-Caricature Mode"
                />
                <span className="option-text">
                  <span className="option-icon">🤪</span>
                  Fun Semi-Caricature Mode
                </span>
                <span className="tooltip">Exaggerates facial features for a fun effect</span>
              </label>
            </div>
          </div>
          
          {error && (
            <div className="error-message" role="alert">
              <span className="error-icon">⚠️</span>
              <p>{error}</p>
            </div>
          )}
        </div>
        
        <div className="image-container">
          <div className="image-box">
            <h2><span className="section-icon">🖼️</span> Original Image</h2>
            <div className="image-preview">
              {originalImage ? (
                <img src={originalImage} alt="Original" className="preview-image" />
              ) : (
                <div className="placeholder">
                  <span className="placeholder-icon">📷</span>
                  <p>No image uploaded</p>
                  <p className="helper-text">Upload an image to get started</p>
                </div>
              )}
            </div>
          </div>
          
          <div className="image-box">
            <h2>
              <span className="section-icon">{caricatureMode ? '🎭' : '🎨'}</span> 
              {caricatureMode ? 'Caricature' : 'Cartoonized'} Image
            </h2>
            <div className="image-preview">
              {loading ? (
                <div className="loading">
                  <div className="progress-container">
                    <div 
                      className="progress-bar" 
                      style={{width: `${progress}%`}}
                      role="progressbar"
                      aria-valuenow={Math.round(progress)}
                      aria-valuemin="0"
                      aria-valuemax="100"
                    ></div>
                  </div>
                  <p>{Math.round(progress)}% complete</p>
                  <div className="spinner"></div>
                  <p>Creating your {caricatureMode ? 'caricature' : 'cartoon'}...</p>
                  {optimizeWithGA && <p className="optimize-note">Genetic optimization in progress...</p>}
                </div>
              ) : finalImage ? (
                <img src={finalImage} alt="Cartoonized" className="preview-image with-shadow" />
              ) : (
                <div className="placeholder">
                  <span className="placeholder-icon">{caricatureMode ? '🎭' : '🎨'}</span>
                  <p>Your {caricatureMode ? 'caricature' : 'cartoon'} will appear here</p>
                  {originalImage && <p className="helper-text">Click the button below to start</p>}
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="action-buttons">
          <button 
            className={`cartoonize-button ${!originalImage || loading ? 'disabled' : ''}`} 
            onClick={handleCartoonize} 
            disabled={!originalImage || loading}
            aria-busy={loading}
          >
            <span className="button-icon">{caricatureMode ? '🎭' : '🎨'}</span>
            {loading ? 'Processing...' : caricatureMode ? 'Create Caricature' : 'Cartoonize Image'}
          </button>
          
          {finalImage && (
            <a 
              href={finalImage} 
              download={caricatureMode ? "caricature.jpg" : "cartoon.jpg"} 
              className="download-button"
              aria-label={`Download ${caricatureMode ? 'Caricature' : 'Cartoon'} image`}
            >
              <span className="button-icon">💾</span>
              Download {caricatureMode ? 'Caricature' : 'Cartoon'}
            </a>
          )}
          
          {originalImage && (
            <button 
              className="reset-button" 
              onClick={() => {
                setOriginalImage(null);
                setFinalImage(null);
                setError(null);
              }}
              aria-label="Reset and start over"
            >
              <span className="button-icon">🔄</span>
              Start Over
            </button>
          )}
        </div>
        
        {!originalImage && (
          <div className="tutorial-section animate-fade-in">
            <h3>How It Works</h3>
            <div className="tutorial-steps">
              <div className="step">
                <div className="step-icon">1️⃣</div>
                <p>Upload your photo</p>
              </div>
              <div className="step">
                <div className="step-icon">2️⃣</div>
                <p>Select processing options</p>
              </div>
              <div className="step">
                <div className="step-icon">3️⃣</div>
                <p>Click "{caricatureMode ? 'Create Caricature' : 'Cartoonize Image'}"</p>
              </div>
              <div className="step">
                <div className="step-icon">4️⃣</div>
                <p>Download your {caricatureMode ? 'caricature' : 'cartoon'}</p>
              </div>
            </div>
          </div>
        )}
      </main>
      
      <footer className="app-footer">
        <p>© 2025 Image Cartoonizer - Bachelor Project</p>
        <div className="footer-links">
          <a href="#about">About</a>
          <a href="#privacy">Privacy</a>
          <a href="#contact">Contact</a>
        </div>
      </footer>
    </div>
  );
}

export default App;