
/**
 * Predefined class names from dataset.yaml
 */
export const CLASS_NAMES = [
  'Nodular BCC',
  'Infiltrative BCC',
  'Superficial BCC',
  'Micronodular BCC',
  'Inflamation/Possible BCC',
  'Hair follicle',
  'Glands',
  'Epidermis'
];

/**
 * Get class number based on class name
 * @param {string} className
 * @returns {number} class index (0-7) or -1 if not found
 */
export const getClassNumber = (className) => {
  return CLASS_NAMES.indexOf(className);
};

/**
 * Get class name based on class number
 * @param {number} classNumber
 * @returns {string} class name or "Unknown" if not found
 */
export const getClassName = (classNumber) => {
  return CLASS_NAMES[classNumber] || "Unknown";
};
