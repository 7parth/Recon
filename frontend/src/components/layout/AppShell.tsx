import { Outlet } from 'react-router-dom';
import { TopNav } from './TopNav';
import { Sidebar } from './Sidebar';
import styles from './AppShell.module.css';

export function AppShell() {
  return (
    <>
      <TopNav />
      <Sidebar />
      <main className={styles.main}>
        <Outlet />
      </main>
    </>
  );
}
