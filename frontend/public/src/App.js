// src/App.js
import React, { useState } from 'react';
import './App.css';

function App() {
  const [originalImage, setOriginalImage] = useState(null);
  const [cartoonImage, setCartoonImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setError(null);
      setCartoonImage(null);
      
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
    }
  };
  
  const handleCartoonize = async () => {
    if (!originalImage) {
      setError("Please upload an image first");
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Create a FormData object to send the image
      const formData = new FormData();
      
      // Convert base64 string back to a file
      const base64Response = await fetch(originalImage);
      const blob = await base64Response.blob();
      const file = new File([blob], "input.jpg", { type: 'image/jpeg' });
      
      formData.append('image', file);
      
      // Send the image to the Python backend
      const response = await fetch('http://localhost:5000/cartoonize', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Cartoonizing failed');
      }
      
      // Get the cartoonized image from the response
      const data = await response.json();
      setCartoonImage(`data:image/jpeg;base64,${data.cartoon_image}`);
    } catch (err) {
      console.error(err);
      setError("Failed to cartoonize image: " + err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Image Cartoonizer</h1>
        <p>Transform your photos into amazing cartoon art using AI!</p>
      </header>
      
      <main className="main-content">
        <div className="upload-section">
          <label className="upload-label">
            <input type="file" accept="image/*" onChange={handleImageUpload} />
            <div className="upload-button">
              <span className="upload-icon">📁</span>
              <span>Upload Image</span>
            </div>
          </label>
          {error && <p className="error-message">{error}</p>}
        </div>
        
        <div className="image-container">
          <div className="image-box">
            <h2>Original Image</h2>
            <div className="image-preview">
              {originalImage ? (
                <img src={originalImage} alt="Original" />
              ) : (
                <div className="placeholder">No image uploaded</div>
              )}
            </div>
          </div>
          
          <div className="image-box">
            <h2>Cartoon Result</h2>
            <div className="image-preview">
              {loading ? (
                <div className="loading">
                  <div className="spinner"></div>
                  <p>Processing your image...</p>
                </div>
              ) : cartoonImage ? (
                <img src={cartoonImage} alt="Cartoonized" />
              ) : (
                <div className="placeholder">No processed image yet</div>
              )}
            </div>
          </div>
        </div>
        
        <div className="action-buttons">
          <button 
            className="cartoonize-button" 
            onClick={handleCartoonize} 
            disabled={!originalImage || loading}
          >
            {loading ? 'Processing...' : 'Cartoonize Image'}
          </button>
          
          {cartoonImage && (
            <a 
              href={cartoonImage} 
              download="cartoon.jpg" 
              className="download-button"
            >
              Download Cartoon
            </a>
          )}
        </div>
      </main>
      
      <footer className="app-footer">
        <p>© 2025 Image Cartoonizer - Bachelor Project</p>
      </footer>
    </div>
  );
}

export default App;