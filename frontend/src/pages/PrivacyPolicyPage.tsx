import React from 'react';
import { LegalDocumentPage } from '../components/legal/LegalDocumentPage';

interface PrivacyPolicyPageProps { theme?: 'light' | 'dark'; }

export const PrivacyPolicyPage: React.FC<PrivacyPolicyPageProps> = () => (
  <LegalDocumentPage kind="privacy" />
);

export default PrivacyPolicyPage;
