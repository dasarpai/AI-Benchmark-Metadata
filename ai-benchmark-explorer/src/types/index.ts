export interface Dataset {
  sno: number;
  dataset_id: string;
  subtask: string;
  task: string;
  associated_tasks: string;
  modalities: string;
  languages: string;
  area: string;
  benchmark_urls: string;
  license: string;
  homepage_url: string;
  pwc_url: string;
  description: string;
  year_published: string;
  paper_title: string;
  paper_url: string;
  dataset_size: string;
  dataset_splits: string;
  num_classes: string;
}

export interface FilterState {
  tasks: string[];
  modalities: string[];
  areas: string[];
  years: string[];
}
