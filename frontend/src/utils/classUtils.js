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

export const getClassNumber = (className) => {
  return CLASS_NAMES.indexOf(className);
};

export const getClassName = (classNumber) => {
  return CLASS_NAMES[classNumber] || "Unknown";
};
