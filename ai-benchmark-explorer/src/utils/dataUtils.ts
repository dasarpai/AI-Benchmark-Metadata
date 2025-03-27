import Papa from 'papaparse';
import { Dataset } from '../types';

export const parseCSV = async (filePath: string): Promise<Dataset[]> => {
  try {
    const response = await fetch(filePath);
    const csvText = await response.text();
    
    return new Promise((resolve, reject) => {
      Papa.parse(csvText, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          const datasets = results.data as Dataset[];
          resolve(datasets);
        },
        error: (error: Error) => {
          reject(error);
        }
      });
    });
  } catch (error) {
    console.error('Error loading CSV file:', error);
    return [];
  }
};

export const getUniqueValues = (data: Dataset[], field: keyof Dataset): string[] => {
  const valueSet = new Set<string>();
  
  data.forEach(item => {
    if (item[field]) {
      // Check if the field value is a string before calling split
      const fieldValue = item[field];
      if (typeof fieldValue === 'string') {
        const values = fieldValue.split(',').map((val: string) => val.trim());
        values.forEach((val: string) => {
          if (val) valueSet.add(val);
        });
      } else if (fieldValue) {
        // If it's not a string but has a value, add it as is
        valueSet.add(String(fieldValue));
      }
    }
  });
  
  return Array.from(valueSet).sort();
};
