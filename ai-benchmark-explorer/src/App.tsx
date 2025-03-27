import React, { useState, useEffect, useMemo } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, Container, Typography, Alert, CircularProgress } from '@mui/material';
import Header from './components/Header';
import FilterPanel from './components/FilterPanel';
import DatasetTable from './components/DatasetTable';
import DatasetDetail from './components/DatasetDetail';
import { Dataset, FilterState } from './types';
import { parseCSV, getUniqueValues } from './utils/dataUtils';

// Create a theme instance
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
});

function App() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    tasks: [],
    modalities: [],
    areas: [],
    years: [],
  });

  // Load data
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        // Try different paths to find the CSV file
        let data: Dataset[] = [];
        try {
          data = await parseCSV('/data/paperswithcode_datasets.csv');
        } catch (e) {
          console.log('Failed to load from /data, trying relative path...');
          try {
            data = await parseCSV('./data/paperswithcode_datasets.csv');
          } catch (e) {
            console.log('Failed to load from ./data, trying direct path...');
            data = await parseCSV('../csv/paperswithcode_datasets.csv');
          }
        }
        
        if (data.length === 0) {
          throw new Error('No data loaded from CSV file');
        }
        
        setDatasets(data);
      } catch (error) {
        console.error('Error loading data:', error);
        setError('Failed to load dataset. Please check the console for details.');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  // Extract unique values for filters
  const availableFilters = useMemo(() => {
    return {
      tasks: getUniqueValues(datasets, 'task'),
      modalities: getUniqueValues(datasets, 'modalities'),
      areas: getUniqueValues(datasets, 'area'),
      years: getUniqueValues(datasets, 'year_published').filter(Boolean),
    };
  }, [datasets]);

  // Apply filters and search
  const filteredDatasets = useMemo(() => {
    return datasets.filter(dataset => {
      // Search query filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const searchableFields = [
          dataset.dataset_id,
          dataset.task,
          dataset.subtask,
          dataset.description,
          dataset.area
        ];
        
        const matchesSearch = searchableFields.some(field => 
          field && field.toLowerCase().includes(query)
        );
        
        if (!matchesSearch) return false;
      }
      
      // Task filter
      if (filters.tasks.length > 0) {
        const datasetTasks = dataset.task.split(',').map(t => t.trim());
        if (!filters.tasks.some(task => datasetTasks.includes(task))) {
          return false;
        }
      }
      
      // Modalities filter
      if (filters.modalities.length > 0) {
        const datasetModalities = dataset.modalities.split(',').map(m => m.trim());
        if (!filters.modalities.some(modality => datasetModalities.includes(modality))) {
          return false;
        }
      }
      
      // Area filter
      if (filters.areas.length > 0 && !filters.areas.includes(dataset.area)) {
        return false;
      }
      
      // Year filter
      if (filters.years.length > 0 && !filters.years.includes(dataset.year_published)) {
        return false;
      }
      
      return true;
    });
  }, [datasets, searchQuery, filters]);

  // Handle dataset selection
  const handleSelectDataset = (dataset: Dataset) => {
    setSelectedDataset(dataset);
    setIsDetailOpen(true);
  };

  // Handle closing the detail modal
  const handleCloseDetail = () => {
    setIsDetailOpen(false);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
        <Header />
        <Container maxWidth="xl" sx={{ py: 3 }}>
          {isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
              <CircularProgress size={60} />
            </Box>
          )}
          
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          {!isLoading && !error && (
            <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
              <Box sx={{ width: { xs: '100%', md: '25%' } }}>
                <FilterPanel
                  filters={filters}
                  setFilters={setFilters}
                  searchQuery={searchQuery}
                  setSearchQuery={setSearchQuery}
                  availableFilters={availableFilters}
                />
              </Box>
              <Box sx={{ width: { xs: '100%', md: '75%' } }}>
                <Box sx={{ 
                  bgcolor: 'background.paper', 
                  p: 3, 
                  borderRadius: 1,
                  boxShadow: 1
                }}>
                  <Typography variant="h5" component="h2" gutterBottom>
                    Datasets {`(${filteredDatasets.length})`}
                  </Typography>
                  <DatasetTable
                    datasets={filteredDatasets}
                    isLoading={false}
                    onSelectDataset={handleSelectDataset}
                  />
                </Box>
              </Box>
            </Box>
          )}
        </Container>
        
        <DatasetDetail
          dataset={selectedDataset}
          isOpen={isDetailOpen}
          onClose={handleCloseDetail}
        />
      </Box>
    </ThemeProvider>
  );
}

export default App;
