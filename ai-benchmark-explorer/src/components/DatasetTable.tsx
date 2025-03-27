import React, { useMemo } from 'react';
import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  TableContainer,
  Box,
  Typography,
  Chip,
  Stack,
  CircularProgress,
  Paper
} from '@mui/material';
import { Dataset } from '../types';

interface DatasetTableProps {
  datasets: Dataset[];
  isLoading: boolean;
  onSelectDataset: (dataset: Dataset) => void;
}

const DatasetTable: React.FC<DatasetTableProps> = ({ 
  datasets, 
  isLoading, 
  onSelectDataset 
}) => {
  const columns = useMemo(() => [
    { Header: 'Name', accessor: 'dataset_id' },
    { Header: 'Task', accessor: 'task' },
    { Header: 'Modalities', accessor: 'modalities' },
    { Header: 'Area', accessor: 'area' },
    { Header: 'Year', accessor: 'year_published' },
  ], []);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (datasets.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
        <Typography variant="h6" color="text.secondary">No datasets found matching your criteria</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', overflow: 'auto' }}>
      <TableContainer component={Paper} elevation={0}>
        <Table size="medium">
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell key={column.accessor}><Typography fontWeight="bold">{column.Header}</Typography></TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {datasets.map((dataset) => (
              <TableRow 
                key={dataset.sno}
                hover
                onClick={() => onSelectDataset(dataset)}
                sx={{ cursor: 'pointer' }}
              >
                <TableCell sx={{ fontWeight: 'medium' }}>{dataset.dataset_id}</TableCell>
                <TableCell>
                  <Typography noWrap>{dataset.task}</Typography>
                </TableCell>
                <TableCell>
                  <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                    {dataset.modalities.split(',').map((modality, index) => (
                      modality.trim() && (
                        <Chip 
                          key={index} 
                          label={modality.trim()} 
                          size="small" 
                          color="primary" 
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      )
                    ))}
                  </Stack>
                </TableCell>
                <TableCell>{dataset.area}</TableCell>
                <TableCell>{dataset.year_published || 'N/A'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default DatasetTable;
