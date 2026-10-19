# Customer retest after repairs

Date: 19 October 2026. Browser-only interaction with the repaired Docker application on port 3110, explicitly in **Reviewer mode**. This is evidence of the customer workflow using supplied synthetic services, not successful live Gemini execution. The original first-time-customer report is preserved separately in `RAHUL_CUSTOMER_REVIEW.md`.

The supplied Jordan Lee account was used; no Rahul account credentials were supplied. Desktop and 390 × 844 browser layouts were exercised. The phone-sized browser view is not a physical-device test.

| Attempt | What was visible | Result |
|---|---|---|
| Sign in | Plain-language sign-in form; supplied Jordan credentials opened the workspace. | Pass |
| Plan and previous bill | Mobile Unlimited, monthly price 65.00; bill period 2026-09, total 65.00 and its actual line item. | Pass; wording in Reviewer mode remains terse. The fixture does not supply a currency. |
| Connection drops after billing inquiry | The first retest incorrectly repeated billing facts. This was repaired, rebuilt and retested in the browser. | Regression captured in `test_dropping_connection_does_not_reuse_previous_billing_intent`. |
| “My internet keeps dropping since yesterday.” | “This account has mobile service, but no home internet service. Did you mean mobile? To check home internet, sign in with the account that owns it.” | Pass |
| “yeah mobile” | Network, diagnostic and XML subscriber results were displayed, including the supplied observation date. A working indicator was visible before the result. | Pass for the supplied services; no claim of live carrier data. |
| Add roaming | “I can't change your plan, add a service or update preferences here. Nothing has been changed.” The reply offered supported alternatives and a support case. | Pass |
| Human-support button | A real saved reference was displayed, with the explicit explanation that the demo does not contact live staff, schedule a callback or provide a response time. | Pass; a reference is not a real callback commitment. |
| Another customer's bill | “Account access denied.” No foreign bill was shown. | Pass |
| Book a taxi | “I can't book taxis or travel. I can help with your account's plan, bill, connection or a support case. No booking has been made.” | Pass |
| Create support case | Approval named ACC-2002, one case, and the requested problem. It explained that this does not change a plan or add a paid service and that no response time is available. | Pass |
| Confirm case | “Support case CASE-EB46F103 is open.” The approval controls disappeared. | Pass; container verification separately checks the actual backend receipt. |
| Sign out and sign in again | Conversation and CASE-EB46F103 were restored. Human-support control still returned a saved reference. | Pass for same-day reauthentication. |

All inspected repaired Reviewer responses appeared within the immediate interaction or next browser-state observation. No precise end-to-end latency measurement or live-provider performance conclusion is claimed. Exact next-day browser behaviour remains unobserved; isolated expiry/reauthentication tests exercise that boundary without changing the computer clock.

Screenshots are stored in `evidence/current/customer-after-desktop.png` and `customer-after-phone.png`. The screenshot mode and test context must accompany any use of these images in a demo.

After applying the repairs, the active application at `http://localhost:3000` was also opened through the browser. It displayed **Live AI**, accepted the supplied Jordan login and returned handoff reference `ESC-5ecab431f974405c973cb9524606087e` from the human-support button. This verifies the model-independent control in live mode, not a Gemini reply. `active-live-handoff.png` records that view. The separate active-upgrade check verified healthy API/enterprise containers, rejected unauthenticated requests and a wrong password, and confirmed no model event occurred during its handoff.

## Remaining customer limitations

The application requires sign-in before account chat. Reviewer answers still contain some diagnostic terminology, including the synthetic XML observation date. Plan changes, paid add-ons, bookings and real staff callbacks are unavailable and are now explained as such. Current live Gemini testing returned HTTP 429; real AI success and response speed therefore remain unverified. These limits must not be presented as completed production services.
