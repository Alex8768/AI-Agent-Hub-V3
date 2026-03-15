import { useContext } from 'react';
import { AppContext } from './appContextStore';
import type { AppContextType } from './appContextStore';

export function useAppContext(): AppContextType {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
}
