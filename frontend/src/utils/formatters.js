/**
 * Format a risk score for display: "64/100"
 */
export function formatRiskScore(score) {
  return `${Math.round(score)}/100`;
}

/**
 * Format a date string to locale-friendly format
 */
export function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

/**
 * Format a datetime string to locale-friendly format with time
 */
export function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Get CSS class for risk level badge
 */
export function getRiskBadgeClass(level) {
  const map = {
    low: 'badge-low',
    moderate: 'badge-moderate',
    elevated: 'badge-elevated',
    high: 'badge-high',
  };
  return `badge ${map[level] || 'badge-neutral'}`;
}

/**
 * Get fill color for risk score bar
 */
export function getRiskColor(level) {
  const map = {
    low: 'var(--color-risk-low)',
    moderate: 'var(--color-risk-moderate)',
    elevated: 'var(--color-risk-elevated)',
    high: 'var(--color-risk-high)',
  };
  return map[level] || 'var(--color-surface-400)';
}

/**
 * Capitalize first letter
 */
export function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, ' ');
}

/**
 * Truncate text
 */
export function truncate(str, max = 80) {
  if (!str || str.length <= max) return str;
  return str.slice(0, max) + '…';
}
