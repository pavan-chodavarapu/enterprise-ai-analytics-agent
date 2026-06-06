# Demo Screenshots

This folder holds the demo GIF used in the README.

## How to generate demo.gif

**Step 1 — Start the app:**
```bash
make run
```

**Step 2 — Record the demo sequence:**

1. Open a screen recorder (Kap on macOS, or peek on Linux)
2. Log in as **alice** — ask: `"What was total revenue in 2001?"`
3. Ask: `"Which store had the highest sales?"`
4. Switch user to **bob** — ask the same question — notice different results
5. Try: `"Show me West region data"` as alice — should return nothing
6. Switch to **admin** — ask: `"Compare revenue across all regions in 2001"`

**Step 3 — Save:**
Save the recording as `demo/screenshots/demo.gif` (keep under 10MB).

**Step 4 — Update README:**
Uncomment the `![Demo]` line at the top of `README.md`.

---

## What to highlight in the GIF

- The user selector in the sidebar (this is the RLS demo)
- alice asking for West region data → empty result (security working)
- admin asking the same question → all regions visible
- The `🔒 RLS active — filtered to: East` note in every result

That 30-second sequence is the entire story of the repo.
