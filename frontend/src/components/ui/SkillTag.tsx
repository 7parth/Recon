import styles from './SkillTag.module.css';

interface SkillTagProps {
  skills: string[];
  maxVisible?: number;
}

export function SkillTag({ skills, maxVisible = 6 }: SkillTagProps) {
  const visible = skills.slice(0, maxVisible);
  const overflow = skills.length - maxVisible;

  return (
    <div className={styles.tags}>
      {visible.map((skill) => (
        <span key={skill} className={styles.tag}>
          {skill}
        </span>
      ))}
      {overflow > 0 && (
        <span className={`${styles.tag} ${styles.overflow}`}>+{overflow} more</span>
      )}
    </div>
  );
}
