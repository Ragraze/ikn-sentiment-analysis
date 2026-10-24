export type Sentiment = 'positive' | 'neutral' | 'negative';
export type Split = 'train' | 'val' | 'test';
export type Counts = Record<Sentiment, number>;
export type Topic = { number: number; words: string[]; word_scores?: number[]; documents?: number };
export type TopicGroup = { topics: Topic[]; coherence: number | null; documents?: number };
export type TopicsResponse = {
  available: boolean;
  source: string | null;
  origin?: 'notebook' | 'trained';
  message?: string;
  groups: Record<Sentiment, TopicGroup>;
};
export type Summary = {
  total: number;
  counts: Counts;
  splits: Record<Split, { count: number; counts: Counts }>;
  preprocessed: Record<Split, number>;
  notebook: { base_model: string; epochs: number; learning_rate: number; max_length: number; batch_size: number };
};
export type Health = {
  ready: boolean;
  state: 'missing_checkpoint' | 'configured' | 'ready' | 'error';
  message: string;
  model: string;
  base_model?: string;
  topics?: {
    model: 'Top2Vec';
    available: boolean;
    groups: Record<Sentiment, { available: boolean; state: 'missing_checkpoint' | 'missing_dependency' | 'configured' | 'ready' | 'error' }>;
  };
};
export type DatasetRow = { id: string; text: string; label: Sentiment; split: Split };
export type DatasetPage = { rows: DatasetRow[]; total: number; page: number; page_size: number };
export type Evaluation = {
  available: boolean;
  message?: string;
  source_file?: string;
  dataset?: string;
  count?: number;
  accuracy?: number;
  macro_f1?: number;
  labels?: Sentiment[];
  confusion?: number[][];
  per_class?: { label: Sentiment; precision: number; recall: number; f1: number; support: number }[];
};
export type Prediction = {
  label: Sentiment;
  scores: Record<Sentiment, number>;
  confidence: number;
  normalized: string;
  model: string;
  base_model: string;
  topic_analysis: TopicAnalysis;
};

export type TopicAnalysis = {
  model: 'Top2Vec';
  sentiment: Sentiment;
  available: boolean;
  matched: boolean;
  state: 'ready' | 'no_match' | 'missing_checkpoint' | 'error';
  message: string;
  topics: (Topic & { similarity: number })[];
};
