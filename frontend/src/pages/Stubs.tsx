export function StubPage({ title }: { title: string }) {
  return (
    <div>
      <h1 style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>{title}</h1>
      <p style={{ color: 'var(--color-text-secondary)' }}>This page is under construction.</p>
    </div>
  );
}

export const Activity = () => <StubPage title="Activity" />;
export const Applications = () => <StubPage title="Applications" />;
export const ReviewQueuePage = () => <StubPage title="Review Queue" />;
export const History = () => <StubPage title="History" />;
export const Keywords = () => <StubPage title="Keywords" />;
export const SavedJobs = () => <StubPage title="Saved Jobs" />;
export const ATSPlatforms = () => <StubPage title="ATS Platforms" />;
export const AutomationLogs = () => <StubPage title="Automation Logs" />;
export const Settings = () => <StubPage title="Settings" />;
export const Integrations = () => <StubPage title="Integrations" />;
