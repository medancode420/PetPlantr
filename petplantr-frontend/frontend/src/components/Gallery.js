import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Chip,
  Button,
  CircularProgress,
  Alert
} from '@mui/material';
import { Favorite, Download, Share } from '@mui/icons-material';
import { petplantrAPI } from '../services/api';

const Gallery = () => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadGallery();
  }, []);

  const loadGallery = async () => {
    try {
      setLoading(true);
      const response = await petplantrAPI.getPublicModels();
      setModels(response.data || []);
    } catch (err) {
      console.error('Failed to load gallery:', err);
      setError('Failed to load gallery. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async (modelId) => {
    try {
      await petplantrAPI.likeModel(modelId, 'anonymous');
      // Refresh gallery to update like counts
      loadGallery();
    } catch (err) {
      console.error('Failed to like model:', err);
    }
  };

  const handleDownload = async (modelId) => {
    try {
      const response = await petplantrAPI.downloadSTL(modelId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `petplantr_model_${modelId}.stl`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
      setError('Failed to download model. Please try again.');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ maxWidth: 600, mx: 'auto', py: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button onClick={loadGallery} variant="outlined">
          Try Again
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Typography variant="h4" component="h2" gutterBottom align="center">
        🖼️ Community Gallery
      </Typography>
      <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
        Discover amazing dog planter designs created by our community
      </Typography>

      {models.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            No models in gallery yet
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Be the first to share your custom planter design!
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {models.map((model) => (
            <Grid item xs={12} sm={6} md={4} key={model.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardMedia
                  component="img"
                  height="200"
                  image={model.thumbnail_url || model.preview_url || '/placeholder-image.jpg'}
                  alt={`${model.breed} planter`}
                  sx={{ objectFit: 'cover' }}
                />
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" component="h3" gutterBottom>
                    {model.title || `${model.breed} Planter`}
                  </Typography>

                  <Box sx={{ mb: 2 }}>
                    <Chip
                      label={`🐕 ${model.breed}`}
                      size="small"
                      color="primary"
                      sx={{ mr: 1, mb: 1 }}
                    />
                    <Chip
                      label={`⭐ ${model.likes || 0} likes`}
                      size="small"
                      variant="outlined"
                      sx={{ mr: 1, mb: 1 }}
                    />
                    <Chip
                      label={`📥 ${model.downloads || 0} downloads`}
                      size="small"
                      variant="outlined"
                      sx={{ mb: 1 }}
                    />
                  </Box>

                  {model.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {model.description}
                    </Typography>
                  )}

                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Button
                      size="small"
                      startIcon={<Favorite />}
                      onClick={() => handleLike(model.id)}
                      variant="outlined"
                    >
                      Like
                    </Button>
                    <Button
                      size="small"
                      startIcon={<Download />}
                      onClick={() => handleDownload(model.id)}
                      variant="outlined"
                    >
                      Download
                    </Button>
                    <Button
                      size="small"
                      startIcon={<Share />}
                      variant="outlined"
                    >
                      Share
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default Gallery;
