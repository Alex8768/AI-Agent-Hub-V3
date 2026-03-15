import { createContext } from 'react';
import type { AnswerResponseDto } from '../contracts/api';

interface GraphNodeLike {
  id?: string;
  name?: string;
  type?: string;
}

interface GraphEdgeLike {
  id?: string;
  src_id?: string;
  dst_id?: string;
  source?: string;
  target?: string;
  rel_type?: string;
}

export interface GraphData {
  nodes: GraphNodeLike[];
  edges: GraphEdgeLike[];
}

export interface AppContextType {
  lastAnswer: AnswerResponseDto | null;
  setLastAnswer: (answer: AnswerResponseDto | null) => void;
  lastGraph: GraphData | null;
  setLastGraph: (graph: GraphData) => void;
}

export const AppContext = createContext<AppContextType | undefined>(undefined);
