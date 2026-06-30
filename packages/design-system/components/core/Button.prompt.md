Evermore's primary interactive control — use for actions ("Share", "Save draft") and, with `href`, for navigation. Filled **primary** is blue; one per view.

```jsx
<Button onClick={save}>Save draft</Button>
<Button variant="secondary">Edit</Button>
<Button variant="tertiary" iconRight="→">See the research</Button>
```

Variants: `primary` (blue fill, hover dims to 0.9), `secondary` (transparent, hairline border that goes solid slate on hover), `tertiary` (link-style blue, underline on hover, no padding), `destructive` (error red). Sizes `sm | md | lg`. Pass `loading` to swap the label for "Sending…" and disable. Don't place two primary buttons side by side — give secondary actions the `secondary` or `tertiary` variant so emphasis comes from fill, not position.
