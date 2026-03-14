import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
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

interface GraphData {
  nodes: GraphNodeLike[];
  edges: GraphEdgeLike[];
}

interface AppContextType {
  lastAnswer: AnswerResponseDto | null;
  setLastAnswer: (answer: AnswerResponseDto | null) => void;
  lastGraph: GraphData | null;
  setLastGraph: (graph: GraphData) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [lastAnswer, setLastAnswer] = useState<AnswerResponseDto | null>(null);
  const [lastGraph, setLastGraph] = useState<GraphData | null>(null);

  return (
    <AppContext.Provider value={{ lastAnswer, setLastAnswer, lastGraph, setLastGraph }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};
