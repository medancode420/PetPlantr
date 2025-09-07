import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Grid,
  Button,
  Alert
} from '@mui/material';
import { Psychology, ArrowBack, Build } from '@mui/icons-material';
import { petplantrAPI } from '../services/api';

const BreedDetection = ({ file, onBreedDetected, onBack }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null);

  const analyzeBreed = useCallback(async () => {
    setIsAnalyzing(true);
    setError(null);
    setProgress(0);

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 300);

      const response = await petplantrAPI.detectBreedFromFile(file, {
        use_tta: true,
        confidence_threshold: 0.8,
        top_k: 5
      });

      clearInterval(progressInterval);
      setProgress(100);
      setResult(response.data);

      // Wait a moment before calling onBreedDetected
      setTimeout(() => {
        onBreedDetected(response.data);
      }, 1000);

    } catch (err) {
      console.error('Breed detection failed:', err);
      setError('Failed to analyze the image. Please try again.');
      setIsAnalyzing(false);
    }
  }, [file, onBreedDetected]);

  useEffect(() => {
    // Create preview of the uploaded file
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);

    // Start analysis
    analyzeBreed();
  }, [file, analyzeBreed]);

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return 'success';
    if (confidence >= 0.7) return 'warning';
    return 'error';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.9) return 'Very High';
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.7) return 'Medium';
    return 'Low';
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={onBack}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4" component="h2">
          🧠 AI Breed Analysis
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {/* Image Preview */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📸 Your Dog's Photo
              </Typography>
              {preview && (
                <Box sx={{ textAlign: 'center' }}>
                  <img
                    src={preview}
                    alt="Dog for analysis"
                    style={{
                      maxWidth: '100%',
                      maxHeight: 300,
                      borderRadius: 8,
                      boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
                    }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Analysis Results */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Psychology sx={{ mr: 1 }} />
                AI Analysis Results
              </Typography>

              {isAnalyzing && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Analyzing your dog's breed...
                  </Typography>
                  <LinearProgress variant="determinate" value={progress} sx={{ mb: 1 }} />
                  <Typography variant="caption" color="text.secondary">
                    {progress}% complete
                  </Typography>
                </Box>
              )}

              {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              )}

              {result && (
                <Box>
                  {/* Primary Breed Result */}
                  <Box sx={{ mb: 3, p: 2, bgcolor: 'success.light', borderRadius: 2 }}>
                    <Typography variant="h5" gutterBottom color="success.dark">
                      🎯 Primary Detection
                    </Typography>
                    <Typography variant="h4" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>
                      {result.predicted_breed}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Chip
                        label={`${(result.confidence * 100).toFixed(1)}% Confidence`}
                        color={getConfidenceColor(result.confidence)}
                        size="small"
                      />
                      <Chip
                        label={getConfidenceLabel(result.confidence)}
                        variant="outlined"
                        size="small"
                      />
                    </Box>
                    {result.is_high_confidence && (
                      <Alert severity="success" sx={{ mt: 1 }}>
                        ✅ High confidence detection - this is likely correct!
                      </Alert>
                    )}
                  </Box>

                  {/* Top Predictions */}
                  {result.top_predictions && result.top_predictions.length > 1 && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        📊 Top Predictions
                      </Typography>
                      {result.top_predictions.slice(1, 5).map((prediction, index) => (
                        <Box
                          key={index}
                          sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            p: 1,
                            mb: 1,
                            borderRadius: 1,
                            bgcolor: 'grey.50'
                          }}
                        >
                          <Typography variant="body1">
                            {Object.keys(prediction)[0]}
                          </Typography>
                          <Chip
                            label={`${(Object.values(prediction)[0] * 100).toFixed(1)}%`}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      ))}
                    </Box>
                  )}

                  {/* Processing Info */}
                  <Box sx={{ p: 2, bgcolor: 'info.light', borderRadius: 2 }}>
                    <Typography variant="body2" color="info.dark">
                      ⚡ Processing time: {result.processing_time?.toFixed(2)} seconds
                    </Typography>
                    <Typography variant="body2" color="info.dark">
                      🤖 Model: {result.model_version || 'CLIP+DPT v2.0'}
                    </Typography>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Next Steps */}
      {result && (
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            🎨 Ready for 3D Generation!
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Your dog's breed has been successfully identified. Now let's create a custom 3D planter design!
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={<Build />}
            onClick={() => onBreedDetected(result)}
            sx={{ px: 4, py: 1.5 }}
          >
            Generate Custom Planter
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default BreedDetection;
