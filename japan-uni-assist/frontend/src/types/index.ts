export interface StudentProfile {
  gpa: number;
  english_type: 'TOEFL' | 'IELTS';
  english_score: number;
  jlpt_level?: 'N1' | 'N2' | 'N3' | 'N4' | 'N5';
  bachelor_school: string;
  bachelor_major: string;
  budget_yen?: number;
  target_major?: string;
}

export interface RecommendItem {
  category: 'REACH' | 'TARGET' | 'SAFETY';
  university_name: string;
  university_name_jp: string;
  program_name: string;
  reason: string;
  match_score: number;
  confidence: number;
  tuition_yen?: number;
  location?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  modelUsed?: string;
  createdAt: string;
}

export interface ChatSession {
  id: string;
  title: string;
  updatedAt: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  supportsStreaming: boolean;
}

export interface User {
  id: string;
  email: string;
  name?: string;
}