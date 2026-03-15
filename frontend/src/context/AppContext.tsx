import React, { useState } from 'react';
import type { ReactNode } from 'react';
import type { AnswerResponseDto } from '../contracts/api';
import type { GraphData } from './appContextStore';
import { AppContext } from './appContextStore';

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [lastAnswer, setLastAnswer] = useState<AnswerResponseDto | null>(null);
  const [lastGraph, setLastGraph] = useState<GraphData | null>(null);

  return (
    <AppContext.Provider value={{ lastAnswer, setLastAnswer, lastGraph, setLastGraph }}>
      {children}
    </AppContext.Provider>
  );
};
