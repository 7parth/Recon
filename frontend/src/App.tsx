import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Dashboard } from './pages/Dashboard';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { ReviewDetail } from './pages/ReviewDetail';
import { JobSearchPage } from './pages/JobSearchPage';
import { ResumesPage } from './pages/ResumesPage';
import { ProfilePage } from './pages/ProfilePage';
import {
  Activity,
  Applications,
  History,
  Keywords,
  SavedJobs,
  ATSPlatforms,
  AutomationLogs,
  Settings,
  Integrations,
} from './pages/Stubs';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="activity" element={<Activity />} />
          <Route path="applications" element={<Applications />} />
          <Route path="review" element={<ReviewQueuePage />} />
          <Route path="review/:threadId" element={<ReviewDetail />} />
          <Route path="history" element={<History />} />
          <Route path="resumes" element={<ResumesPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="keywords" element={<Keywords />} />
          <Route path="jobs/search" element={<JobSearchPage />} />
          <Route path="jobs/saved" element={<SavedJobs />} />
          <Route path="automation/ats" element={<ATSPlatforms />} />
          <Route path="automation/logs" element={<AutomationLogs />} />
          <Route path="settings" element={<Settings />} />
          <Route path="integrations" element={<Integrations />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
