import { Outlet } from 'react-router-dom';
import { TopNav } from './TopNav';
import { Sidebar } from './Sidebar';
import { DashboardDataContext, useDashboardDataProvider } from '../../hooks/useDashboardData';
import styles from './AppShell.module.css';

export function AppShell() {
  const value = useDashboardDataProvider();

  return (
    <DashboardDataContext.Provider value={value}>
      <TopNav />
      <Sidebar />
      <main className={styles.main}>
        <Outlet />
      </main>
    </DashboardDataContext.Provider>
  );
}
