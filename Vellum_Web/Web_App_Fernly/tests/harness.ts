import assert from "node:assert/strict";
export { describe, it } from "node:test";

export function expect<T>(actual: T) {
  return {
    toBe: (expected: unknown) => assert.strictEqual(actual, expected),
    toEqual: (expected: unknown) => assert.deepStrictEqual(actual, expected),
    toContain: (item: unknown) => {
      if (typeof actual === "string") {
        assert.ok(actual.includes(String(item)), `Expected "${actual}" to contain "${String(item)}"`);
      } else if (Array.isArray(actual)) {
        assert.ok(
          actual.includes(item),
          `Expected array to contain ${JSON.stringify(item)}, got ${JSON.stringify(actual)}`
        );
      } else {
        assert.fail("toContain called on non-string, non-array");
      }
    },
    not: {
      toContain: (item: unknown) => {
        if (typeof actual === "string") {
          assert.ok(!actual.includes(String(item)), `Expected "${actual}" not to contain "${String(item)}"`);
        } else if (Array.isArray(actual)) {
          assert.ok(
            !actual.includes(item),
            `Expected array not to contain ${JSON.stringify(item)}`
          );
        }
      },
    },
    toHaveProperty: (prop: string, val?: unknown) => {
      assert.ok(
        actual && typeof actual === "object" && prop in (actual as Record<string, unknown>),
        `Expected property "${prop}" in object`
      );
      if (val !== undefined) {
        assert.deepStrictEqual((actual as Record<string, unknown>)[prop], val);
      }
    },
    toBeGreaterThan: (val: number) => {
      assert.ok(Number(actual) > val, `Expected ${String(actual)} > ${val}`);
    },
    toBeGreaterThanOrEqual: (val: number) => {
      assert.ok(Number(actual) >= val, `Expected ${String(actual)} >= ${val}`);
    },
    toBeLessThanOrEqual: (val: number) => {
      assert.ok(Number(actual) <= val, `Expected ${String(actual)} <= ${val}`);
    },
    toBeDefined: () => {
      assert.ok(actual !== undefined, "Expected value to be defined");
    },
  };
}
