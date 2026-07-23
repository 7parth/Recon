import {
  LayoutDashboard,
  Activity,
  Briefcase,
  Clock,
  History,
  FileText,
  User,
  Tag,
  Search,
  Bookmark,
  Settings2,
  ScrollText,
  Settings,
  Puzzle,
} from 'lucide-react';
import { NavLink } from 'react-router-dom';
import styles from './Sidebar.module.css';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  badge?: number;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const NAV: NavSection[] = [
  {
    title: 'Overview',
    items: [
      { to: '/', label: 'Dashboard', icon: <LayoutDashboard size={16} strokeWidth={1.5} /> },
      { to: '/activity', label: 'Activity', icon: <Activity size={16} strokeWidth={1.5} /> },
    ],
  },
  {
    title: 'Applications',
    items: [
      { to: '/applications', label: 'All Applications', icon: <Briefcase size={16} strokeWidth={1.5} /> },
      { to: '/review', label: 'Review Queue', icon: <Clock size={16} strokeWidth={1.5} />, badge: 3 },
      { to: '/history', label: 'History', icon: <History size={16} strokeWidth={1.5} /> },
    ],
  },
  {
    title: 'Resume & Profile',
    items: [
      { to: '/resumes', label: 'Resumes', icon: <FileText size={16} strokeWidth={1.5} /> },
      { to: '/profile', label: 'Profile', icon: <User size={16} strokeWidth={1.5} /> },
      { to: '/keywords', label: 'Skills & Keywords', icon: <Tag size={16} strokeWidth={1.5} /> },
    ],
  },
  {
    title: 'Job Discovery',
    items: [
      { to: '/jobs/search', label: 'Search Jobs', icon: <Search size={16} strokeWidth={1.5} /> },
      { to: '/jobs/saved', label: 'Saved Jobs', icon: <Bookmark size={16} strokeWidth={1.5} /> },
    ],
  },
  {
    title: 'Automation',
    items: [
      { to: '/automation/ats', label: 'ATS Platforms', icon: <Settings2 size={16} strokeWidth={1.5} /> },
      { to: '/automation/logs', label: 'Automation Logs', icon: <ScrollText size={16} strokeWidth={1.5} /> },
    ],
  },
  {
    title: 'Settings',
    items: [
      { to: '/settings', label: 'Preferences', icon: <Settings size={16} strokeWidth={1.5} /> },
      { to: '/integrations', label: 'Integrations', icon: <Puzzle size={16} strokeWidth={1.5} /> },
    ],
  },
];

export function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <nav className={styles.nav}>
        {NAV.map((section) => (
          <div key={section.title} className={styles.section}>
            <p className={styles.sectionTitle}>{section.title}</p>
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `${styles.navItem} ${isActive ? styles.active : ''}`
                }
              >
                <span className={styles.icon}>{item.icon}</span>
                <span className={styles.itemLabel}>{item.label}</span>
                {item.badge !== undefined && (
                  <span className={styles.badge}>{item.badge}</span>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className={styles.footer}>
        <div className={styles.avatar}>R</div>
        <div className={styles.userInfo}>
          <span className={styles.userName}>Rishabh Sharma</span>
          <span className={styles.userEmail}>rishabh@example.com</span>
        </div>
        <button className={styles.moreBtn} aria-label="User menu">···</button>
      </div>
    </aside>
  );
}
