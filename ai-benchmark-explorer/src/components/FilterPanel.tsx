import React from 'react';
import {
  Box,
  Typography,
  Checkbox,
  FormGroup,
  FormControlLabel,
  TextField,
  InputAdornment,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
  Stack
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { FilterState } from '../types';

interface FilterPanelProps {
  filters: FilterState;
  setFilters: React.Dispatch<React.SetStateAction<FilterState>>;
  searchQuery: string;
  setSearchQuery: React.Dispatch<React.SetStateAction<string>>;
  availableFilters: {
    tasks: string[];
    modalities: string[];
    areas: string[];
    years: string[];
  };
}

const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  setFilters,
  searchQuery,
  setSearchQuery,
  availableFilters,
}) => {
  const handleFilterChange = (filterType: keyof FilterState, value: string, checked: boolean) => {
    setFilters(prev => {
      const currentValues = [...prev[filterType]];
      if (checked) {
        return { ...prev, [filterType]: [...currentValues, value] };
      } else {
        return { ...prev, [filterType]: currentValues.filter(item => item !== value) };
      }
    });
  };

  return (
    <Paper
      elevation={1}
      sx={{
        p: 3,
        width: '100%',
        maxHeight: 'calc(100vh - 120px)',
        overflowY: 'auto'
      }}
    >
      <Stack spacing={3}>
        <Typography variant="h6">Search & Filter</Typography>
        
        <TextField
          placeholder="Search datasets..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          fullWidth
          size="small"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon color="action" />
              </InputAdornment>
            ),
          }}
        />

        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography fontWeight="medium">Task</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <FormGroup sx={{ maxHeight: '200px', overflowY: 'auto' }}>
              {availableFilters.tasks.map((task) => (
                <FormControlLabel
                  key={task}
                  control={
                    <Checkbox 
                      checked={filters.tasks.includes(task)}
                      onChange={(e) => handleFilterChange('tasks', task, e.target.checked)}
                      color="primary"
                      size="small"
                    />
                  }
                  label={task}
                />
              ))}
            </FormGroup>
          </AccordionDetails>
        </Accordion>

        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography fontWeight="medium">Modalities</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <FormGroup sx={{ maxHeight: '200px', overflowY: 'auto' }}>
              {availableFilters.modalities.map((modality) => (
                <FormControlLabel
                  key={modality}
                  control={
                    <Checkbox 
                      checked={filters.modalities.includes(modality)}
                      onChange={(e) => handleFilterChange('modalities', modality, e.target.checked)}
                      color="primary"
                      size="small"
                    />
                  }
                  label={modality}
                />
              ))}
            </FormGroup>
          </AccordionDetails>
        </Accordion>

        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography fontWeight="medium">Area</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <FormGroup sx={{ maxHeight: '200px', overflowY: 'auto' }}>
              {availableFilters.areas.map((area) => (
                <FormControlLabel
                  key={area}
                  control={
                    <Checkbox 
                      checked={filters.areas.includes(area)}
                      onChange={(e) => handleFilterChange('areas', area, e.target.checked)}
                      color="primary"
                      size="small"
                    />
                  }
                  label={area}
                />
              ))}
            </FormGroup>
          </AccordionDetails>
        </Accordion>

        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography fontWeight="medium">Year Published</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <FormGroup sx={{ maxHeight: '200px', overflowY: 'auto' }}>
              {availableFilters.years.map((year) => (
                <FormControlLabel
                  key={year}
                  control={
                    <Checkbox 
                      checked={filters.years.includes(year)}
                      onChange={(e) => handleFilterChange('years', year, e.target.checked)}
                      color="primary"
                      size="small"
                    />
                  }
                  label={year}
                />
              ))}
            </FormGroup>
          </AccordionDetails>
        </Accordion>
      </Stack>
    </Paper>
  );
};

export default FilterPanel;
