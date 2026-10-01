// Shared branch catalogue — codes match backend BRANCH_NAMES.
export const BRANCHES = [
  { code: 'CSD', name: 'Computer Science (Data)' },
  { code: 'CSE', name: 'Computer Science' },
  { code: 'CSA', name: 'Computer Science (AI)' },
  { code: 'ECE', name: 'Electronics & Communication' },
  { code: 'EEE', name: 'Electrical & Electronics' },
  { code: 'MEC', name: 'Mechanical' },
  { code: 'CIV', name: 'Civil' },
];

export const branchName = (code) => BRANCHES.find((b) => b.code === code)?.name ?? code;

export const BATCHES = [22, 23, 24, 25];

// 25MVCSD0327 = batch 25 + college MV + branch CSD + serial 0327
export function splitRoll(roll) {
  const m = /^(\d{2})([A-Z]{2})([A-Z]{3})(\d{4})$/.exec((roll || '').toUpperCase());
  if (!m) return null;
  return { batch: m[1], college: m[2], branch: m[3], serial: m[4] };
}
