import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Dashboard } from './pages/Dashboard';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { ReviewDetail } from './pages/ReviewDetail';
import { JobSearchPage } from './pages/JobSearchPage';
import { ResumesPage } from './pages/ResumesPage';
import { ProfilePage } from './pages/ProfilePage';
import { ApplicationsPage } from './pages/ApplicationsPage';
import { ActivityPage } from './pages/ActivityPage';
import { KeywordsPage } from './pages/KeywordsPage';
import { SettingsPage } from './pages/SettingsPage';
import { IntegrationsPage } from './pages/IntegrationsPage';
import { SavedJobsPage } from './pages/SavedJobsPage';
import { AutomationLogsPage } from './pages/AutomationLogsPage';
import { ATSPlatformsPage } from './pages/ATSPlatformsPage';
import { HistoryPage } from './pages/HistoryPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="activity" element={<ActivityPage />} />
          <Route path="applications" element={<ApplicationsPage />} />
          <Route path="review" element={<ReviewQueuePage />} />
          <Route path="review/:threadId" element={<ReviewDetail />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="resumes" element={<ResumesPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="keywords" element={<KeywordsPage />} />
          <Route path="jobs/search" element={<JobSearchPage />} />
          <Route path="jobs/saved" element={<SavedJobsPage />} />
          <Route path="automation/ats" element={<ATSPlatformsPage />} />
          <Route path="automation/logs" element={<AutomationLogsPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="integrations" element={<IntegrationsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
