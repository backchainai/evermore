Evermore's primary layout surface — a flat white card with a hairline border and no shadow. Use it for panels, records, and content blocks. Shadows are reserved for floating UI (menus, popovers, modals).

```jsx
<Card>
  <h3>Sally's records</h3>
  <p>Select traits to include.</p>
</Card>

<Card interactive onClick={open}>…</Card>
```

`padding` is `sm | md | lg`. Pass `interactive` for clickable cards — they gain a pointer, raise their border alpha, and lift `translateY(-2px)` on hover. Use `as` to render a `section`/`article`/`button`.
