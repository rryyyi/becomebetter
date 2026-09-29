# Repository Instructions

## Verification After Code Changes

- After every code change, run an appropriate verification before considering the change complete.
- For UI changes, launch or otherwise inspect the affected UI and check for visible display, layout, and interaction bugs. Include relevant viewport sizes when practical.
- For backend changes, run the affected service or tests and verify that the changed functionality works end to end where practical.
- If verification cannot be run, state what was not verified and why.

## Push Every Code Change

- After each code change has been verified, commit it and push it to the configured Git remote.
- Do not claim a change was pushed unless the push succeeded.
- If no remote is configured, or a commit or push fails, report the blocker clearly. Do not invent or guess a remote destination; ask for the required configuration when needed.
