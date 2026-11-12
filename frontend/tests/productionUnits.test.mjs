import test from 'node:test';
import assert from 'node:assert/strict';
import { compatibleUnits } from '../src/utils/productionUnits.js';

test('production supports only dimensionally compatible mass and volume units', () => {
  assert.deepEqual(compatibleUnits('KG'), ['G', 'KG', 'QUINTAL', 'TON']);
  assert.deepEqual(compatibleUnits('L'), ['ML', 'L']);
  assert.deepEqual(compatibleUnits('PCS'), ['PCS']);
  assert.deepEqual(compatibleUnits('UNKNOWN'), []);
});
