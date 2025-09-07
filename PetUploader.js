import React, { useState } from 'react';
import axios from 'axios';

const PetUploader = () => {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a pet photo first');
      return;
    }

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/upload-pet-photo/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
    } catch (error) {
      console.error('Upload failed:', error);
      setError(error.response?.data?.detail || 'Failed to process pet photo');
    }
    setLoading(false);
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type.startsWith('image/')) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a valid image file');
      setFile(null);
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '20px' }}>
      <h2>🐾 Generate Your Pet's Custom Planter</h2>
      <p>Upload a photo of your pet and we'll create a personalized 3D planter design!</p>

      <form onSubmit={handleUpload} style={{ marginBottom: '20px' }}>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            style={{ marginBottom: '10px', display: 'block' }}
          />
          {file && (
            <div>
              <p>Selected: {file.name}</p>
              <img
                src={URL.createObjectURL(file)}
                alt="Preview"
                style={{ maxWidth: '200px', maxHeight: '200px', border: '1px solid #ccc' }}
              />
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={loading || !file}
          style={{
            padding: '10px 20px',
            backgroundColor: loading ? '#ccc' : '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Generating Planter...' : 'Generate Pet Planter!'}
        </button>
      </form>

      {error && (
        <div style={{
          color: '#d32f2f',
          backgroundColor: '#ffebee',
          padding: '10px',
          borderRadius: '5px',
          marginBottom: '20px'
        }}>
          ❌ {error}
        </div>
      )}

      {result && (
        <div style={{
          border: '1px solid #4CAF50',
          borderRadius: '10px',
          padding: '20px',
          backgroundColor: '#f9f9f9'
        }}>
          <h3>🎉 Your Custom Pet Planter is Ready!</h3>
          <p><strong>Detected Breed:</strong> {result.breed}</p>

          <div style={{ margin: '20px 0' }}>
            <h4>Planter Preview:</h4>
            <img
              src={result.planter_image}
              alt="Generated Planter"
              style={{
                maxWidth: '100%',
                border: '2px solid #4CAF50',
                borderRadius: '10px'
              }}
            />
          </div>

          <div style={{ marginTop: '20px' }}>
            <a
              href={result.stl_url}
              download
              style={{
                display: 'inline-block',
                padding: '10px 20px',
                backgroundColor: '#2196F3',
                color: 'white',
                textDecoration: 'none',
                borderRadius: '5px',
                marginRight: '10px'
              }}
            >
              📥 Download STL for 3D Printing
            </a>
          </div>

          {result.note && (
            <p style={{ fontStyle: 'italic', color: '#666', marginTop: '10px' }}>
              Note: {result.note}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default PetUploader;
