const MASS_UNITS = ['G', 'KG', 'QUINTAL', 'TON'];
const VOLUME_UNITS = ['ML', 'L'];

export function compatibleUnits(baseUnit) {
  if (MASS_UNITS.includes(baseUnit)) return [...MASS_UNITS];
  if (VOLUME_UNITS.includes(baseUnit)) return [...VOLUME_UNITS];
  return baseUnit === 'PCS' ? ['PCS'] : [];
}
