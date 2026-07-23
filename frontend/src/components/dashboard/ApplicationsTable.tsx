import { MoreHorizontal } from 'lucide-react';
import { Badge, statusToBadge } from '../ui/Badge';
import styles from './ApplicationsTable.module.css';

export interface ApplicationRow {
  id: string;
  jobTitle: string;
  company: string;
  matchScore: number;
  status: string;
  appliedOn: string;
  logoLetter: string;
  logoColor: string;
}

interface ApplicationsTableProps {
  applications: ApplicationRow[];
}

export function ApplicationsTable({ applications }: ApplicationsTableProps) {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.sectionLabel}>Recent Applications</span>
        <button className={styles.viewAll}>VIEW ALL &rarr;</button>
      </div>

      <div className={styles.table}>
        <div className={`${styles.row} ${styles.tableHeader}`}>
          <div className={styles.colPosition}>POSITION</div>
          <div className={styles.colCompany}>COMPANY</div>
          <div className={styles.colScore}>MATCH SCORE</div>
          <div className={styles.colStatus}>STATUS</div>
          <div className={styles.colDate}>APPLIED ON</div>
          <div className={styles.colAction}></div>
        </div>

        {applications.map((app) => (
          <div key={app.id} className={styles.row}>
            <div className={styles.colPosition}>
              <div className={styles.jobInfo}>
                <div className={styles.logo} style={{ background: app.logoColor }}>
                  {app.logoLetter}
                </div>
                <div>
                  <div className={styles.jobTitle}>{app.jobTitle}</div>
                  <div className={styles.jobCompany}>{app.company}</div>
                </div>
              </div>
            </div>
            <div className={`${styles.colCompany} ${styles.cell}`}>{app.company}</div>
            <div className={`${styles.colScore} ${styles.cell}`}>
              <span className={styles.monoScore}>{app.matchScore}%</span>
            </div>
            <div className={`${styles.colStatus} ${styles.cell}`}>
              <Badge variant={statusToBadge(app.status)} />
            </div>
            <div className={`${styles.colDate} ${styles.cell}`}>
              <span className={styles.monoDate}>{app.appliedOn}</span>
            </div>
            <div className={`${styles.colAction} ${styles.cell}`}>
              <button className={styles.actionBtn}>
                <MoreHorizontal size={16} strokeWidth={2} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
