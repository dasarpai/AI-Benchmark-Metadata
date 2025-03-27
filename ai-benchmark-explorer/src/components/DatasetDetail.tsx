import React from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions,
  Typography,
  Button,
  Box,
  Chip,
  Link,
  Divider,
  IconButton,
  Stack,
  Paper
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import LaunchIcon from '@mui/icons-material/Launch';
import { Dataset } from '../types';

interface DatasetDetailProps {
  dataset: Dataset | null;
  isOpen: boolean;
  onClose: () => void;
}

const DatasetDetail: React.FC<DatasetDetailProps> = ({ dataset, isOpen, onClose }) => {
  if (!dataset) return null;

  const {
    dataset_id,
    description,
    task,
    subtask,
    associated_tasks,
    modalities,
    homepage_url,
    pwc_url,
    year_published,
    area,
    dataset_size,
    license,
    languages,
    paper_url,
  } = dataset;

  const formatTasks = (tasks: string) => {
    if (!tasks) return [];
    return tasks.split(',').map(task => task.trim()).filter(Boolean);
  };

  const associatedTasks = formatTasks(associated_tasks);
  const modalitiesList = formatTasks(modalities);

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      scroll="paper"
    >
      <DialogTitle sx={{ pr: 6 }}>
        <Typography variant="h5">{dataset_id}</Typography>
        <IconButton
          aria-label="close"
          onClick={onClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>Task</Typography>
          <Chip label={task} size="small" />
          {subtask && subtask !== task && (
            <Chip label={subtask} size="small" sx={{ ml: 1 }} />
          )}
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>Description</Typography>
          <Typography variant="body1">{description || 'No description available'}</Typography>
        </Box>

        <Divider sx={{ my: 3 }} />

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
          <Box sx={{ width: { xs: '100%', md: 'calc(50% - 12px)' } }}>
            <Paper elevation={0} sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">Area</Typography>
              <Typography variant="body1">{area || 'N/A'}</Typography>
            </Paper>
          </Box>
          <Box sx={{ width: { xs: '100%', md: 'calc(50% - 12px)' } }}>
            <Paper elevation={0} sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">Year Published</Typography>
              <Typography variant="body1">{year_published || 'N/A'}</Typography>
            </Paper>
          </Box>
          <Box sx={{ width: { xs: '100%', md: 'calc(50% - 12px)' } }}>
            <Paper elevation={0} sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">Dataset Size</Typography>
              <Typography variant="body1">{dataset_size || 'N/A'}</Typography>
            </Paper>
          </Box>
          <Box sx={{ width: { xs: '100%', md: 'calc(50% - 12px)' } }}>
            <Paper elevation={0} sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">License</Typography>
              <Typography variant="body1">{license || 'N/A'}</Typography>
            </Paper>
          </Box>
          <Box sx={{ width: '100%' }}>
            <Paper elevation={0} sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">Modalities</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                {modalitiesList.length > 0 ? 
                  modalitiesList.map((modality, index) => (
                    <Chip key={index} label={modality} size="small" />
                  )) : 
                  <Typography variant="body2">No modalities available</Typography>
                }
              </Box>
            </Paper>
          </Box>
          <Box sx={{ width: '100%' }}>
            <Paper elevation={0} sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">Associated Tasks</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                {associatedTasks.length > 0 ? 
                  associatedTasks.map((task, index) => (
                    <Chip key={index} label={task} size="small" />
                  )) : 
                  <Typography variant="body2">No associated tasks available</Typography>
                }
              </Box>
            </Paper>
          </Box>
          <Box sx={{ width: '100%' }}>
            <Paper elevation={0} sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">Languages</Typography>
              <Typography variant="body1">{languages || 'N/A'}</Typography>
            </Paper>
          </Box>
        </Box>

        <Divider sx={{ my: 3 }} />

        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>External Links</Typography>
          <Stack spacing={2}>
            {homepage_url && (
              <Link 
                href={homepage_url} 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
              >
                <Typography variant="body1">Homepage</Typography>
                <LaunchIcon fontSize="small" />
              </Link>
            )}
            {pwc_url && (
              <Link 
                href={pwc_url} 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
              >
                <Typography variant="body1">Papers With Code</Typography>
                <LaunchIcon fontSize="small" />
              </Link>
            )}
            {paper_url && (
              <Link 
                href={paper_url} 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
              >
                <Typography variant="body1">Research Paper</Typography>
                <LaunchIcon fontSize="small" />
              </Link>
            )}
          </Stack>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DatasetDetail;
