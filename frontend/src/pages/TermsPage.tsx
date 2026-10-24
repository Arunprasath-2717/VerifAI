import React from 'react';
import { LegalDocumentPage } from '../components/legal/LegalDocumentPage';

interface TermsPageProps { theme?: 'light' | 'dark'; }

export const TermsPage: React.FC<TermsPageProps> = () => (
  <LegalDocumentPage kind="terms" />
);

export default TermsPage;
