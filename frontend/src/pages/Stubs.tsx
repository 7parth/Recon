/* Remaining stub pages — to be replaced in future phases */
import { useNavigate } from 'react-router-dom';

export function StubPage({ title }: { title: string }) {
  return (
    <div>
      <h1 style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>{title}</h1>
      <p style={{ color: 'var(--color-text-secondary)' }}>This page is under construction.</p>
    </div>
  );
}

/* History: alias to Applications (/applications) for now */
export function History() {
  const navigate = useNavigate();
  // Redirect to Applications page which shows full history
  return (
    <div>
      <h1 style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, textTransform: 'uppercase', marginBottom: 'var(--space-4)' }}>History</h1>
      <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-4)' }}>
        Full application history is available on the All Applications page.
      </p>
      <button
        onClick={() => navigate('/applications')}
        style={{
          background: 'var(--color-accent)',
          border: 'none',
          borderRadius: 'var(--radius-sm)',
          color: '#fff',
          fontFamily: 'var(--font-sans)',
          fontSize: 'var(--text-base)',
          fontWeight: 600,
          padding: '8px 16px',
          cursor: 'pointer',
        }}
      >
        Go to All Applications →
      </button>
    </div>
  );
}

