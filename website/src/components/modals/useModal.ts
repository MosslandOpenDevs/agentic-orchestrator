'use client';

import { useContext } from 'react';
import { ModalContext, type ModalType, type ModalData } from './ModalProvider';

export type { ModalType, ModalData };

export function useModal() {
  const context = useContext(ModalContext);
  if (!context) {
    throw new Error('useModal must be used within ModalProvider');
  }
  return context;
}
