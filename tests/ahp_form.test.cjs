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
