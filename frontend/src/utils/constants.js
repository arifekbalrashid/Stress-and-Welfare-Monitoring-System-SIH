export const ROLES = {
  PERSONNEL: 'personnel',
  WELFARE_OFFICER: 'welfare_officer',
  COMMANDER: 'commander',
  ADMIN: 'admin',
};

export const RISK_LEVELS = {
  LOW: 'low',
  MODERATE: 'moderate',
  ELEVATED: 'elevated',
  HIGH: 'high',
};

export const RISK_LEVEL_LABELS = {
  low: 'Low',
  moderate: 'Moderate',
  elevated: 'Elevated',
  high: 'High',
};

export const RISK_LEVEL_COLORS = {
  low: 'badge-low',
  moderate: 'badge-moderate',
  elevated: 'badge-elevated',
  high: 'badge-high',
};

export const TREND_LABELS = {
  increasing: 'Increasing',
  stable: 'Stable',
  decreasing: 'Decreasing',
};

export const WELLNESS_QUESTIONS = [
  { key: 'sleep_quality', label: 'Sleep quality', description: 'How would you rate your sleep quality this week?' },
  { key: 'energy_level', label: 'Energy level', description: 'How would you describe your energy levels?' },
  { key: 'workload_perception', label: 'Perceived workload', description: 'How manageable has your workload felt?' },
  { key: 'wellbeing', label: 'Overall wellbeing', description: 'How would you rate your overall wellbeing?' },
  { key: 'recovery', label: 'Recovery', description: 'How well have you been able to recover between duties?' },
];

export const SCALE_LABELS = {
  1: 'Very low',
  2: 'Low',
  3: 'Moderate',
  4: 'Good',
  5: 'Very good',
};

export const ROLE_ROUTES = {
  [ROLES.PERSONNEL]: '/p/dashboard',
  [ROLES.WELFARE_OFFICER]: '/w/cases',
  [ROLES.COMMANDER]: '/c/overview',
  [ROLES.ADMIN]: '/a/personnel',
};

export const DISCLAIMER_TEXT = '';
