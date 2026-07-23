import { Check, User, Circle } from 'lucide-react';
import styles from './PipelineStepper.module.css';

export type StepStatus = 'done' | 'active' | 'pending';

export interface PipelineStep {
  key: string;
  label: string;
  status: StepStatus;
}

interface PipelineStepperProps {
  steps: PipelineStep[];
}

export function PipelineStepper({ steps }: PipelineStepperProps) {
  return (
    <div className={styles.stepper}>
      {steps.map((step, i) => (
        <div key={step.key} className={styles.stepWrapper}>
          {/* Connecting line before */}
          {i > 0 && (
            <div
              className={`${styles.line} ${steps[i - 1].status === 'done' ? styles.lineDone : styles.linePending}`}
            />
          )}

          <div className={`${styles.step} ${styles[step.status]}`}>
            <div className={`${styles.node} ${styles[`node_${step.status}`]}`}>
              {step.status === 'done' && <Check size={10} strokeWidth={3} />}
              {step.status === 'active' && <User size={10} strokeWidth={2} />}
              {step.status === 'pending' && <Circle size={8} strokeWidth={2} fill="currentColor" />}
            </div>
            <span className={styles.stepLabel}>{step.label}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
