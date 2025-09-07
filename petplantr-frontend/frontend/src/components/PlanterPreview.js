import React, { useState, useRef } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  LinearProgress,
  Alert,
  Button
} from '@mui/material';
import { Build, Download, ViewInAr, Settings, ArrowBack } from '@mui/icons-material';
import { petplantrAPI } from '../services/api';

const PlanterPreview = ({ breedResult, onGenerationComplete, onBack }) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [generationResult, setGenerationResult] = useState(null);
  const [error, setError] = useState(null);
  const [settings, setSettings] = useState({
    style: 'realistic',
    size: 'medium',
    quality: 'high',
    pattern: 'none',
    include_ear_tabs: true
  });

  const fileInputRef = useRef(null);

  const handleSettingChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleGenerate = async () => {
    if (!fileInputRef.current?.files[0]) {
      setError('Please select an image file first');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setProgress(0);

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 5, 95));
      }, 1000);

      const response = await petplantrAPI.generatePlanter(fileInputRef.current.files[0], {
        breed_hint: breedResult.predicted_breed,
        ...settings
      });

      clearInterval(progressInterval);
      setProgress(100);
      setGenerationResult(response.data);

      // Wait a moment before calling onGenerationComplete
      setTimeout(() => {
        onGenerationComplete(response.data);
      }, 1000);

    } catch (err) {
      console.error('Generation failed:', err);
      setError('Failed to generate planter. Please try again.');
      setIsGenerating(false);
    }
  };

  const handleDownload = async (jobId) => {
    try {
      const response = await petplantrAPI.downloadSTL(jobId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `petplantr_${jobId}.stl`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
      setError('Failed to download STL file. Please try again.');
    }
  };

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={onBack}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4" component="h2">
          🎨 Custom Planter Generation
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {/* Settings Panel */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Settings sx={{ mr: 1 }} />
                Generation Settings
              </Typography>

              <Box sx={{ mb: 3 }}>
                <Chip
                  label={`🐕 ${breedResult.predicted_breed}`}
                  color="primary"
                  sx={{ mb: 2 }}
                />
                <Typography variant="body2" color="text.secondary">
                  Confidence: {(breedResult.confidence * 100).toFixed(1)}%
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Style</InputLabel>
                  <Select
                    value={settings.style}
                    label="Style"
                    onChange={(e) => handleSettingChange('style', e.target.value)}
                  >
                    <MenuItem value="realistic">Realistic</MenuItem>
                    <MenuItem value="cartoon">Cartoon</MenuItem>
                    <MenuItem value="minimalist">Minimalist</MenuItem>
                    <MenuItem value="abstract">Abstract</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small">
                  <InputLabel>Size</InputLabel>
                  <Select
                    value={settings.size}
                    label="Size"
                    onChange={(e) => handleSettingChange('size', e.target.value)}
                  >
                    <MenuItem value="small">Small (10cm)</MenuItem>
                    <MenuItem value="medium">Medium (15cm)</MenuItem>
                    <MenuItem value="large">Large (20cm)</MenuItem>
                    <MenuItem value="xlarge">Extra Large (25cm)</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small">
                  <InputLabel>Quality</InputLabel>
                  <Select
                    value={settings.quality}
                    label="Quality"
                    onChange={(e) => handleSettingChange('quality', e.target.value)}
                  >
                    <MenuItem value="standard">Standard</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="ultra-high">Ultra High</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small">
                  <InputLabel>Pattern</InputLabel>
                  <Select
                    value={settings.pattern}
                    label="Pattern"
                    onChange={(e) => handleSettingChange('pattern', e.target.value)}
                  >
                    <MenuItem value="none">None</MenuItem>
                    <MenuItem value="waves">Waves</MenuItem>
                    <MenuItem value="dots">Dots</MenuItem>
                    <MenuItem value="hearts">Hearts</MenuItem>
                    <MenuItem value="stars">Stars</MenuItem>
                  </Select>
                </FormControl>
              </Box>

              <Box sx={{ mt: 3 }}>
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="image/*"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    if (e.target.files[0]) {
                      // File is ready for generation
                    }
                  }}
                />
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => fileInputRef.current?.click()}
                  sx={{ mb: 2 }}
                >
                  Select Image File
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Preview & Generation */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <ViewInAr sx={{ mr: 1 }} />
                3D Planter Preview
              </Typography>

              {/* 3D Preview Placeholder */}
              <Box
                sx={{
                  height: 400,
                  bgcolor: 'grey.100',
                  borderRadius: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mb: 3,
                  border: '2px dashed',
                  borderColor: 'grey.300'
                }}
              >
                <Box sx={{ textAlign: 'center' }}>
                  <ViewInAr sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    3D Preview Coming Soon
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Interactive 3D visualization will be available here
                  </Typography>
                </Box>
              </Box>

              {isGenerating && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body1" gutterBottom>
                    🔄 Generating your custom planter...
                  </Typography>
                  <LinearProgress variant="determinate" value={progress} sx={{ mb: 1 }} />
                  <Typography variant="caption" color="text.secondary">
                    {progress}% complete - This may take a few minutes
                  </Typography>
                </Box>
              )}

              {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              )}

              {generationResult && (
                <Box sx={{ mb: 3 }}>
                  <Alert severity="success" sx={{ mb: 2 }}>
                    ✅ Your custom planter has been generated successfully!
                  </Alert>

                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <Button
                      variant="contained"
                      startIcon={<Download />}
                      onClick={() => handleDownload(generationResult.job_id)}
                    >
                      Download STL File
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<ViewInAr />}
                      onClick={() => window.open(generationResult.preview_url, '_blank')}
                    >
                      View Preview
                    </Button>
                  </Box>

                  <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                    <Typography variant="body2" color="info.dark">
                      📊 Job ID: {generationResult.job_id}
                    </Typography>
                    <Typography variant="body2" color="info.dark">
                      ⏱️ Processing Time: {generationResult.processing_time || 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="info.dark">
                      📏 Quality Score: {generationResult.quality_score || 'N/A'}
                    </Typography>
                  </Box>
                </Box>
              )}

              {!isGenerating && !generationResult && (
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h6" gutterBottom>
                    🚀 Ready to Generate!
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Click the button below to create your custom 3D planter design
                  </Typography>
                  <Button
                    variant="contained"
                    size="large"
                    startIcon={<Build />}
                    onClick={handleGenerate}
                    disabled={!fileInputRef.current?.files[0]}
                    sx={{ px: 4, py: 1.5 }}
                  >
                    Generate Custom Planter
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PlanterPreview;
