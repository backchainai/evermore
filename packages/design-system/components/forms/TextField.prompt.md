Labelled text input — the form workhorse. Set `multiline` for a textarea. The blue focus ring, error, and success states are built in.

```jsx
<TextField label="Animal name" required placeholder="e.g. Sally" />
<TextField label="Bio" multiline hint="Lead with behaviour, not looks." />
<TextField label="Email" error="Enter a valid email" />
```

States: default, focus (blue ring), `error` (red, ▲ icon), `success` (green, ✓ icon), and disabled. Always pass a `label`; use `hint` for guidance and `error`/`success` for validation — each pairs an icon with text so meaning never rests on color alone.
