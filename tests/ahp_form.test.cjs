const test = require('node:test');
const assert = require('node:assert/strict');
const { decode, encode, describe } = require('../static/ahp-form.js');

test('all 17 AHP values round-trip including reciprocal and intermediate scales', () => {
  const values = ['1', ...Array.from({ length: 8 }, (_, i) => String(i + 2)),
    ...Array.from({ length: 8 }, (_, i) => `1/${i + 2}`)];
  for (const value of values) {
    const { direction, magnitude } = decode(value);
    assert.equal(encode(direction, magnitude), value);
  }
});

test('incomplete or invalid answers never become equal importance automatically', () => {
  for (const value of ['', '0', '10', '1/1', '1/10', '2.5', 'unexpected']) {
    assert.equal(decode(value).direction, '');
  }
  assert.equal(encode('left', null), '');
  assert.equal(encode('right', null), '');
  assert.equal(encode('', 5), '');
  assert.equal(encode('left', 3.5), '');
  assert.equal(encode('equal', null), '1');
});

test('summary names the selected criterion correctly in both directions', () => {
  assert.equal(describe('5', 'Pengungsi', 'Kerusakan'),
    'Pengungsi lebih penting secara kuat daripada Kerusakan.');
  assert.equal(describe('1/5', 'Pengungsi', 'Kerusakan'),
    'Kerusakan lebih penting secara kuat daripada Pengungsi.');
  assert.equal(describe('1', 'Pengungsi', 'Kerusakan'),
    'Pengungsi dan Kerusakan sama penting.');
});

test('intermediate summary retains direction, scale, and full criterion names', () => {
  const text = describe('1/6', 'Jumlah pengungsi', 'Jarak posko induk ke titik gempa');
  assert.ok(text.startsWith('Jarak posko induk ke titik gempa lebih penting daripada Jumlah pengungsi'));
  assert.ok(text.includes('skala 6'));
  assert.ok(describe('', 'A', 'B').startsWith('Belum dijawab'));
});

test('criteria order warns only when the chosen direction contradicts the ranking', () => {
  const { orderConflict } = require('../static/ahp-form.js');
  const order = [2, 0, 1, 3, 4, 5]; // C3 paling penting, lalu C1, C2, ...
  assert.equal(orderConflict(order, 0, 1, '5'), null);
  assert.deepEqual(orderConflict(order, 0, 1, '1/5'), { expected: 0, chosen: 1 });
  assert.deepEqual(orderConflict(order, 0, 2, '3'), { expected: 2, chosen: 0 });
  assert.equal(orderConflict(order, 0, 2, '1/3'), null);
  assert.equal(orderConflict(order, 0, 2, '1'), null);
  assert.equal(orderConflict(order, 0, 2, ''), null);
  assert.equal(orderConflict(null, 0, 2, '9'), null);
});

test('ranking helpers move items without mutating and reject invalid stored orders', () => {
  const { moveItem, validOrder } = require('../static/ahp-form.js');
  const order = [0, 1, 2, 3, 4, 5];
  assert.deepEqual(moveItem(order, 3, 0), [3, 0, 1, 2, 4, 5]);
  assert.deepEqual(moveItem(order, 0, -1), order);
  assert.deepEqual(order, [0, 1, 2, 3, 4, 5]);
  assert.ok(validOrder(order, 6));
  for (const bad of [[0, 1, 2], [0, 0, 1, 2, 3, 4], [0, 1, 2, 3, 4, 6], '012345', null]) {
    assert.equal(validOrder(bad, 6), false);
  }
});

test('transitive estimate combines earlier answers and never invents one without basis', () => {
  const { transitiveEstimate, farFromEstimate, nearestSaaty } = require('../static/ahp-form.js');
  // C1 vs C2 = 3 (C1 lebih penting), C2 vs C3 = 3  =>  C1 vs C3 sekitar 9
  const answers = { '0-1': '3', '1-2': '3' };
  const estimate = transitiveEstimate(answers, 0, 2, 6);
  assert.equal(estimate.value, '9');
  assert.deepEqual(estimate.via, [1]);
  assert.equal(farFromEstimate('1', estimate), true);
  assert.equal(farFromEstimate('1/3', estimate), true);
  assert.equal(farFromEstimate('7', estimate), false);
  assert.equal(farFromEstimate('', estimate), false);
  // Arah sebaliknya dibaca sebagai resiprokal: C3 vs C1 dari sudut pasangan (0,2) tetap konsisten.
  assert.equal(transitiveEstimate({ '0-1': '1/3', '1-2': '1/3' }, 0, 2, 6).value, '1/9');
  assert.equal(transitiveEstimate({ '0-1': '3' }, 0, 2, 6), null);
  assert.equal(transitiveEstimate({}, 0, 2, 6), null);
  assert.equal(nearestSaaty(1), '1');
  assert.equal(nearestSaaty(100), '9');
  assert.equal(nearestSaaty(1 / 4.2), '1/4');
  assert.deepEqual(answers, { '0-1': '3', '1-2': '3' });
});
