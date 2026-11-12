export function hasPositiveStock(value) {
  const quantity = typeof value === 'string' ? value.trim() : String(value ?? '');
  return /^\d+(?:\.\d+)?$/.test(quantity) && /[1-9]/.test(quantity);
}
