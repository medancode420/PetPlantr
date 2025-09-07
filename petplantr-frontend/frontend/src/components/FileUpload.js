import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Paper,
  Button,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Chip
} from '@mui/material';
import { CloudUpload, PhotoCamera, CheckCircle } from '@mui/icons-material';

const FileUpload = ({ onFileSelect }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setError(null);

    if (rejectedFiles.length > 0) {
      setError('Please select a valid image file (JPG, PNG, JPEG)');
      return;
    }

    const file = acceptedFiles[0];
    if (file) {
      setSelectedFile(file);

      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target.result);
      reader.readAsDataURL(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleContinue = () => {
    if (selectedFile) {
      setIsProcessing(true);
      // Simulate processing time
      setTimeout(() => {
        setIsProcessing(false);
        onFileSelect(selectedFile);
      }, 1000);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreview(null);
    setError(null);
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h4" component="h2" gutterBottom align="center">
        📸 Upload Your Dog's Photo
      </Typography>
      <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
        Choose a clear photo of your dog for the best AI breed detection results
      </Typography>

      {!selectedFile ? (
        <Paper
          {...getRootProps()}
          sx={{
            p: 4,
            textAlign: 'center',
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'grey.300',
            backgroundColor: isDragActive ? 'primary.50' : 'grey.50',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            '&:hover': {
              borderColor: 'primary.main',
              backgroundColor: 'primary.50',
            },
          }}
        >
          <input {...getInputProps()} />
          <CloudUpload sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive ? 'Drop your dog photo here' : 'Drag & drop your dog photo here'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            or click to browse files
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Supports: JPG, PNG, JPEG, WebP (max 10MB)
          </Typography>
        </Paper>
      ) : (
        <Card>
          <CardContent>
            <Box sx={{ textAlign: 'center' }}>
              {preview && (
                <Box sx={{ mb: 3 }}>
                  <img
                    src={preview}
                    alt="Dog preview"
                    style={{
                      maxWidth: '100%',
                      maxHeight: 300,
                      borderRadius: 8,
                      boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
                    }}
                  />
                </Box>
              )}

              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
                <CheckCircle sx={{ color: 'success.main', mr: 1 }} />
                <Typography variant="h6" color="success.main">
                  Photo Selected Successfully!
                </Typography>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                File: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </Typography>

              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                <Button
                  variant="outlined"
                  onClick={handleReset}
                  disabled={isProcessing}
                >
                  Choose Different Photo
                </Button>
                <Button
                  variant="contained"
                  onClick={handleContinue}
                  disabled={isProcessing}
                  startIcon={isProcessing ? <CircularProgress size={20} /> : <PhotoCamera />}
                >
                  {isProcessing ? 'Processing...' : 'Continue to AI Analysis'}
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom>
          ✨ What happens next?
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Chip label="1. AI analyzes your dog's breed" variant="outlined" />
          <Chip label="2. Custom 3D planter design generated" variant="outlined" />
          <Chip label="3. Download STL file for 3D printing" variant="outlined" />
        </Box>
      </Box>
    </Box>
  );
};

export default FileUpload;
