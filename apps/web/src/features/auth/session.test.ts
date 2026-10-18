import { expect, test } from "bun:test";
import { decodeSession } from "./session";
const session = {
  customerId: "CUST-1001",
  accountId: "ACC-2001",
  roles: ["customer"],
  mode: "REVIEWER",
  state: "NEW",
  history: [],
  pendingAction: null,
};
test("accepts the complete login and restored-session contract", () => {
  expect(decodeSession(session)).toEqual(session);
});
test("rejects partial responses before rendering the signed-in workspace", () => {
  for (const payload of [
    null,
    {},
    { customerId: "CUST-1001", mode: "REVIEWER" },
    { ...session, roles: null },
    { ...session, history: [{ role: "assistant", text: null }] },
    { ...session, mode: "unknown" },
  ])
    expect(() => decodeSession(payload)).toThrow();
});
