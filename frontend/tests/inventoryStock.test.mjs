import assert from 'node:assert/strict';
import test from 'node:test';
import { hasPositiveStock } from '../src/utils/inventoryStock.js';

test('badge counts positive decimal balances and excludes zero-stock rows', () => {
  const balances = ['12.000000', '0.000000', '0.000001', '0'];
  assert.equal(balances.filter(hasPositiveStock).length, 2);
});

test('invalid and negative balances are not counted as stock', () => {
  assert.equal(hasPositiveStock('-1.000000'), false);
  assert.equal(hasPositiveStock('invalid'), false);
  assert.equal(hasPositiveStock(null), false);
});
