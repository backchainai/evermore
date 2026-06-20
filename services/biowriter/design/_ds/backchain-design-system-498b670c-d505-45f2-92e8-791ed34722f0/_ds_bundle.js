/* @ds-bundle: {"format":3,"namespace":"BackchainDesignSystem_498b67","components":[{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Card","sourcePath":"components/core/Card.jsx"},{"name":"SectionLabel","sourcePath":"components/core/SectionLabel.jsx"},{"name":"StatGrid","sourcePath":"components/core/StatGrid.jsx"},{"name":"StyledList","sourcePath":"components/core/StyledList.jsx"},{"name":"TextField","sourcePath":"components/forms/TextField.jsx"},{"name":"SiteFooter","sourcePath":"components/navigation/SiteFooter.jsx"},{"name":"SiteHeader","sourcePath":"components/navigation/SiteHeader.jsx"}],"sourceHashes":{"components/core/Badge.jsx":"1454d8ec1e09","components/core/Button.jsx":"595e56b82c3f","components/core/Card.jsx":"75681e19aa58","components/core/SectionLabel.jsx":"7dabc6c45a3c","components/core/StatGrid.jsx":"a219672d672f","components/core/StyledList.jsx":"ce30159c304f","components/forms/TextField.jsx":"6d1dcfea90fb","components/navigation/SiteFooter.jsx":"59d7868a83a0","components/navigation/SiteHeader.jsx":"4e2d416b97ac","source/tokens/tailwind_preset.mjs":"e05ac68c79a2","ui_kits/backchain-website/Approach.jsx":"e5c2e4068c38","ui_kits/backchain-website/Contact.jsx":"4780759187c0","ui_kits/backchain-website/Hero.jsx":"5502290f9d64","ui_kits/backchain-website/Services.jsx":"ff78961c7c08","ui_kits/backchain-website/tweaks-panel.jsx":"6591467622ed"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.BackchainDesignSystem_498b67 = window.BackchainDesignSystem_498b67 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/core/Badge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
let injected = false;
function useBadgeStyles() {
  if (injected || typeof document === 'undefined') return;
  injected = true;
  const css = `
  .bc-badge {
    display: inline-flex; align-items: center; gap: 0.375rem;
    height: 24px; padding: 0 var(--space-xs);
    font-family: var(--font-content); font-size: var(--text-small);
    font-weight: var(--weight-medium); line-height: 1;
    border-radius: var(--radius-pill); white-space: nowrap;
  }
  .bc-badge--neutral { background: color-mix(in srgb, var(--color-gray) 20%, transparent); color: var(--color-heading); }
  .bc-badge--accent  { background: color-mix(in srgb, var(--color-coral) 12%, transparent); color: var(--color-cta); }
  .bc-badge--success { background: color-mix(in srgb, var(--color-success) 15%, transparent); color: #1e7e45; }
  .bc-badge--error   { background: color-mix(in srgb, var(--color-error) 15%, transparent); color: var(--color-error); }
  `;
  const el = document.createElement('style');
  el.setAttribute('data-bc', 'badge');
  el.textContent = css;
  document.head.appendChild(el);
}

/**
 * Badge / Tag — small inline label for status, category, or metadata.
 */
function Badge({
  variant = 'neutral',
  className = '',
  children,
  ...rest
}) {
  useBadgeStyles();
  return /*#__PURE__*/React.createElement("span", _extends({
    className: `bc-badge bc-badge--${variant} ${className}`.trim()
  }, rest), children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/* Inject component CSS once. Keeps the primitive self-contained while
 * letting :hover / :focus-visible / :active states use real CSS. */
let injected = false;
function useButtonStyles() {
  if (injected || typeof document === 'undefined') return;
  injected = true;
  const css = `
  .bc-btn {
    display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
    font-family: var(--font-content); font-weight: var(--weight-medium);
    border-radius: var(--radius-md); border: 1px solid transparent;
    cursor: pointer; text-decoration: none; white-space: nowrap;
    transition: background-color var(--duration-default) var(--ease-in-out),
                border-color var(--duration-default) var(--ease-in-out),
                color var(--duration-default) var(--ease-in-out),
                opacity var(--duration-default) var(--ease-in-out),
                transform var(--duration-fast) var(--ease-out);
  }
  .bc-btn:active { transform: scale(0.98); }
  .bc-btn:focus-visible { outline: 2px solid var(--color-focus-ring); outline-offset: 2px; }
  .bc-btn[aria-disabled="true"], .bc-btn:disabled { opacity: 0.5; cursor: not-allowed; pointer-events: none; }

  /* sizes */
  .bc-btn--sm { height: 40px; padding: 0 1rem; font-size: var(--text-small); }
  .bc-btn--md { height: 48px; padding: 0 1.5rem; font-size: var(--text-body); }
  .bc-btn--lg { height: 56px; padding: 0 1.75rem; font-size: var(--text-body); }

  /* primary */
  .bc-btn--primary { background: var(--color-cta); color: var(--color-cta-text); }
  .bc-btn--primary:hover { opacity: 0.9; text-decoration: none; }

  /* secondary */
  .bc-btn--secondary { background: transparent; color: var(--color-heading); border-color: var(--border-btn-2); }
  .bc-btn--secondary:hover { border-color: var(--color-heading); text-decoration: none; }

  /* tertiary */
  .bc-btn--tertiary { background: transparent; color: var(--color-cta); padding-left: 0; padding-right: 0; height: auto; }
  .bc-btn--tertiary:hover { text-decoration: underline; }

  /* destructive */
  .bc-btn--destructive { background: var(--color-error); color: var(--color-cream); }
  .bc-btn--destructive:hover { opacity: 0.9; }
  `;
  const el = document.createElement('style');
  el.setAttribute('data-bc', 'button');
  el.textContent = css;
  document.head.appendChild(el);
}

/**
 * Backchain Button — primary interactive primitive.
 * Renders a <button> by default, or an <a> when `href` is provided.
 */
function Button({
  variant = 'primary',
  size = 'md',
  href,
  disabled = false,
  loading = false,
  loadingLabel = 'Sending…',
  iconRight,
  className = '',
  children,
  ...rest
}) {
  useButtonStyles();
  const cls = `bc-btn bc-btn--${variant} bc-btn--${size} no-underline ${className}`.trim();
  const content = loading ? loadingLabel : children;
  const node = /*#__PURE__*/React.createElement(React.Fragment, null, content, iconRight && !loading ? /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true"
  }, iconRight) : null);
  if (href && !disabled) {
    return /*#__PURE__*/React.createElement("a", _extends({
      className: cls,
      href: href
    }, rest), node);
  }
  return /*#__PURE__*/React.createElement("button", _extends({
    className: cls,
    disabled: disabled || loading,
    "aria-disabled": disabled || loading ? 'true' : undefined,
    "aria-busy": loading ? 'true' : undefined
  }, rest), node);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/Card.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
let injected = false;
function useCardStyles() {
  if (injected || typeof document === 'undefined') return;
  injected = true;
  const css = `
  .bc-card {
    background: var(--color-surface);
    border: 1px solid var(--border-card);
    border-radius: var(--radius-lg);
    transition: border-color var(--duration-default) var(--ease-in-out),
                transform var(--duration-default) var(--ease-out);
  }
  .bc-card--sm { padding: var(--space-md); }
  .bc-card--md { padding: var(--space-lg); }
  .bc-card--lg { padding: var(--space-xl); }
  .bc-card--interactive { cursor: pointer; }
  .bc-card--interactive:hover { border-color: var(--border-card-hover); transform: translateY(-2px); }
  .bc-card--interactive:focus-visible { outline: 2px solid var(--color-focus-ring); outline-offset: 2px; }
  `;
  const el = document.createElement('style');
  el.setAttribute('data-bc', 'card');
  el.textContent = css;
  document.head.appendChild(el);
}

/**
 * Backchain Card — the primary layout primitive. Flat off-white surface
 * with a hairline alpha border. No drop shadow (reserved for floating UI).
 * Wrap in a `.on-slate` ancestor and it composites as alpha-cream.
 */
function Card({
  padding = 'md',
  interactive = false,
  as: Tag = 'div',
  className = '',
  children,
  ...rest
}) {
  useCardStyles();
  const cls = `bc-card bc-card--${padding} ${interactive ? 'bc-card--interactive' : ''} ${className}`.trim();
  const interactiveProps = interactive ? {
    tabIndex: 0
  } : {};
  return /*#__PURE__*/React.createElement(Tag, _extends({
    className: cls
  }, interactiveProps, rest), children);
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Card.jsx", error: String((e && e.message) || e) }); }

// components/core/SectionLabel.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Section Label (Eyebrow) — small uppercase kicker above a heading.
 * Deep coral, 12px, Medium, wide tracking. Signals section identity.
 */
function SectionLabel({
  as: Tag = 'p',
  className = '',
  style,
  children,
  ...rest
}) {
  const base = {
    fontFamily: 'var(--font-content)',
    fontSize: 'var(--text-xs)',
    fontWeight: 'var(--weight-medium)',
    textTransform: 'uppercase',
    letterSpacing: 'var(--letter-spacing-wide)',
    color: 'var(--color-label-accent)',
    margin: 0
  };
  return /*#__PURE__*/React.createElement(Tag, _extends({
    className: className,
    style: {
      ...base,
      ...style
    }
  }, rest), children);
}
Object.assign(__ds_scope, { SectionLabel });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/SectionLabel.jsx", error: String((e && e.message) || e) }); }

// components/core/StatGrid.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Stat Grid — grid of big deep-coral numerals with small gray captions.
 * The brand's proof-point pattern (IPOs, growth, uptime). On a `.on-slate`
 * band, numerals render cream and captions cream/70.
 */
function StatGrid({
  stats = [],
  columns = 3,
  className = '',
  style,
  ...rest
}) {
  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
    gap: 'var(--space-lg)',
    ...style
  };
  const numeral = {
    fontFamily: 'var(--font-content)',
    fontSize: 'var(--text-h1)',
    fontWeight: 'var(--weight-semibold)',
    color: 'var(--color-label-accent)',
    lineHeight: 1.1,
    letterSpacing: 'var(--letter-spacing-tight)'
  };
  const caption = {
    fontSize: 'var(--text-small)',
    color: 'var(--color-body)',
    lineHeight: 'var(--line-height-snug)',
    marginTop: 'var(--space-xs)'
  };
  return /*#__PURE__*/React.createElement("div", _extends({
    className: className,
    style: gridStyle
  }, rest), stats.map((s, i) => /*#__PURE__*/React.createElement("div", {
    key: i
  }, /*#__PURE__*/React.createElement("div", {
    style: numeral
  }, s.value), /*#__PURE__*/React.createElement("div", {
    style: caption
  }, s.label))));
}
Object.assign(__ds_scope, { StatGrid });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/StatGrid.jsx", error: String((e && e.message) || e) }); }

// components/core/StyledList.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Styled List — feature / "what's included" list using a deep-coral em-dash
 * marker instead of a bullet. Not for navigation.
 */
function StyledList({
  items = [],
  className = '',
  style,
  ...rest
}) {
  const ul = {
    listStyle: 'none',
    margin: 0,
    padding: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--space-xs)',
    ...style
  };
  const li = {
    display: 'flex',
    gap: 'var(--space-sm)',
    color: 'var(--color-body)',
    fontSize: 'var(--text-body)',
    lineHeight: 'var(--line-height-normal)'
  };
  const marker = {
    color: 'var(--color-label-accent)',
    flexShrink: 0,
    marginTop: '0.05em',
    fontWeight: 500
  };
  return /*#__PURE__*/React.createElement("ul", _extends({
    className: className,
    style: ul
  }, rest), items.map((item, i) => /*#__PURE__*/React.createElement("li", {
    key: i,
    style: li
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: marker
  }, "\u2014"), /*#__PURE__*/React.createElement("span", null, item))));
}
Object.assign(__ds_scope, { StyledList });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/StyledList.jsx", error: String((e && e.message) || e) }); }

// components/forms/TextField.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
let injected = false;
function useFieldStyles() {
  if (injected || typeof document === 'undefined') return;
  injected = true;
  const css = `
  .bc-field { display: flex; flex-direction: column; gap: 0.375rem; }
  .bc-field__label { font-family: var(--font-content); font-size: var(--text-small); font-weight: var(--weight-medium); color: var(--color-heading); }
  .bc-field__req { color: var(--color-cta); margin-left: 2px; }
  .bc-field__control {
    font-family: var(--font-content); font-size: var(--text-body); color: var(--color-heading);
    background: var(--color-canvas); border: 1px solid var(--border-input);
    border-radius: var(--radius-sm); padding: 0 0.875rem; min-height: 48px; width: 100%;
    transition: border-color var(--duration-default) var(--ease-in-out), box-shadow var(--duration-default) var(--ease-in-out);
  }
  textarea.bc-field__control { padding: 0.75rem 0.875rem; min-height: 120px; line-height: var(--line-height-normal); resize: vertical; }
  .bc-field__control::placeholder { color: color-mix(in srgb, var(--color-gray) 55%, transparent); }
  .bc-field__control:focus { outline: none; border-color: transparent; box-shadow: 0 0 0 2px var(--color-focus-ring); }
  .bc-field--error .bc-field__control { border-width: 2px; border-color: var(--color-error); }
  .bc-field--success .bc-field__control { border-width: 2px; border-color: var(--color-success); }
  .bc-field__control:disabled { background: color-mix(in srgb, var(--color-gray) 30%, transparent); color: color-mix(in srgb, var(--color-charcoal) 50%, transparent); cursor: not-allowed; }
  .bc-field__msg { display: flex; align-items: center; gap: 0.375rem; font-size: var(--text-small); line-height: var(--line-height-snug); }
  .bc-field__msg--error { color: var(--color-error); }
  .bc-field__msg--success { color: #1e7e45; }
  .bc-field__hint { font-size: var(--text-small); color: var(--color-body); }
  `;
  const el = document.createElement('style');
  el.setAttribute('data-bc', 'field');
  el.textContent = css;
  document.head.appendChild(el);
}
let idSeq = 0;
function useFieldId(provided) {
  const ref = React.useRef(provided);
  if (!ref.current) ref.current = `bc-field-${++idSeq}`;
  return ref.current;
}

/**
 * TextField — labelled text input (or textarea via `multiline`). Shares the
 * full state system: default / focus / error / success / disabled. Errors
 * and successes pair an icon with text (never color alone).
 */
function TextField({
  label,
  id,
  required = false,
  error = null,
  success = null,
  hint = null,
  multiline = false,
  className = '',
  ...rest
}) {
  useFieldStyles();
  const fieldId = useFieldId(id);
  const describedBy = error ? `${fieldId}-err` : success ? `${fieldId}-ok` : hint ? `${fieldId}-hint` : undefined;
  const state = error ? 'error' : success ? 'success' : '';
  const Control = multiline ? 'textarea' : 'input';
  return /*#__PURE__*/React.createElement("div", {
    className: `bc-field ${state ? `bc-field--${state}` : ''} ${className}`.trim()
  }, label ? /*#__PURE__*/React.createElement("label", {
    className: "bc-field__label",
    htmlFor: fieldId
  }, label, required ? /*#__PURE__*/React.createElement("span", {
    className: "bc-field__req",
    "aria-hidden": "true"
  }, "*") : null) : null, /*#__PURE__*/React.createElement(Control, _extends({
    id: fieldId,
    className: "bc-field__control",
    "aria-required": required || undefined,
    "aria-invalid": error ? 'true' : undefined,
    "aria-describedby": describedBy
  }, rest)), hint && !error && !success ? /*#__PURE__*/React.createElement("span", {
    id: `${fieldId}-hint`,
    className: "bc-field__hint"
  }, hint) : null, error ? /*#__PURE__*/React.createElement("span", {
    id: `${fieldId}-err`,
    role: "alert",
    className: "bc-field__msg bc-field__msg--error"
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true"
  }, "\u25B2"), error) : null, success ? /*#__PURE__*/React.createElement("span", {
    id: `${fieldId}-ok`,
    className: "bc-field__msg bc-field__msg--success"
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true"
  }, "\u2713"), success) : null);
}
Object.assign(__ds_scope, { TextField });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/TextField.jsx", error: String((e && e.message) || e) }); }

// components/navigation/SiteFooter.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
let injected = false;
function useFooterStyles() {
  if (injected || typeof document === 'undefined') return;
  injected = true;
  const css = `
  .bc-footer { background: var(--color-canvas); border-top: 1px solid var(--border-divider); }
  .bc-footer__inner { max-width: var(--layout-max-width); margin: 0 auto; padding: var(--space-2xl) var(--space-lg) var(--space-xl); display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: var(--space-xl); }
  .bc-footer__brand img { height: 30px; width: auto; display: block; margin-bottom: var(--space-md); }
  .bc-footer__wordmark { font-family: var(--font-brand); font-weight: 700; font-size: 1.5rem; color: var(--color-heading); margin-bottom: var(--space-sm); }
  .bc-footer__tag { font-size: var(--text-small); color: var(--color-body); max-width: 34ch; line-height: var(--line-height-normal); }
  .bc-footer__col h4 { font-family: var(--font-content); font-size: var(--text-xs); font-weight: var(--weight-medium); text-transform: uppercase; letter-spacing: var(--letter-spacing-wide); color: var(--color-label-accent); margin: 0 0 var(--space-md); }
  .bc-footer__col ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-sm); }
  .bc-footer__col a { font-size: var(--text-small); color: var(--color-body); }
  .bc-footer__col a:hover { color: var(--color-link-hover); }
  .bc-footer__bar { max-width: var(--layout-max-width); margin: 0 auto; padding: var(--space-md) var(--space-lg); border-top: 1px solid var(--border-divider); display: flex; justify-content: space-between; align-items: center; gap: var(--space-md); flex-wrap: wrap; }
  .bc-footer__bar span { font-size: var(--text-small); color: var(--color-body); }
  @media (max-width: 720px) { .bc-footer__inner { grid-template-columns: 1fr; gap: var(--space-lg); } }
  `;
  const el = document.createElement('style');
  el.setAttribute('data-bc', 'footer');
  el.textContent = css;
  document.head.appendChild(el);
}

/**
 * Site Footer — brand + tagline, link columns, and a bottom legal bar.
 */
function SiteFooter({
  logoSrc,
  tagline = 'Discover where AI works. 25 years of platform engineering, now helping small teams automate what matters.',
  columns = [],
  legal = `© ${new Date().getFullYear()} Backchain LLC`,
  email = 'chris@backchain.ai',
  className = '',
  ...rest
}) {
  useFooterStyles();
  return /*#__PURE__*/React.createElement("footer", _extends({
    className: `bc-footer ${className}`.trim()
  }, rest), /*#__PURE__*/React.createElement("div", {
    className: "bc-footer__inner"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-footer__brand"
  }, logoSrc ? /*#__PURE__*/React.createElement("img", {
    src: logoSrc,
    alt: "Backchain"
  }) : /*#__PURE__*/React.createElement("div", {
    className: "bc-footer__wordmark"
  }, "Backchain"), /*#__PURE__*/React.createElement("p", {
    className: "bc-footer__tag"
  }, tagline)), columns.map((col, i) => /*#__PURE__*/React.createElement("div", {
    className: "bc-footer__col",
    key: i
  }, /*#__PURE__*/React.createElement("h4", null, col.title), /*#__PURE__*/React.createElement("ul", null, col.links.map((l, j) => /*#__PURE__*/React.createElement("li", {
    key: j
  }, /*#__PURE__*/React.createElement("a", {
    className: "no-underline",
    href: l.href
  }, l.label))))))), /*#__PURE__*/React.createElement("div", {
    className: "bc-footer__bar"
  }, /*#__PURE__*/React.createElement("span", null, legal), /*#__PURE__*/React.createElement("a", {
    className: "no-underline",
    href: `mailto:${email}`
  }, email)));
}
Object.assign(__ds_scope, { SiteFooter });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/SiteFooter.jsx", error: String((e && e.message) || e) }); }

// components/navigation/SiteHeader.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
let injected = false;
function useHeaderStyles() {
  if (injected || typeof document === 'undefined') return;
  injected = true;
  const css = `
  .bc-header { width: 100%; background: color-mix(in srgb, var(--color-canvas) 85%, transparent); backdrop-filter: saturate(1.1) blur(8px); border-bottom: 1px solid var(--border-divider); }
  .bc-header__inner { max-width: var(--layout-max-width); margin: 0 auto; height: var(--header-height-sm); padding: 0 var(--space-lg); display: flex; align-items: center; justify-content: space-between; gap: var(--space-lg); }
  .bc-header__brand { display: inline-flex; align-items: center; gap: 0.625rem; }
  .bc-header__brand img { height: 30px; width: auto; display: block; }
  .bc-header__wordmark { font-family: var(--font-brand); font-weight: 700; font-size: 1.4rem; color: var(--color-heading); letter-spacing: .005em; }
  .bc-header__nav { display: flex; align-items: center; gap: var(--space-lg); }
  .bc-header__links { display: flex; align-items: center; gap: var(--space-lg); }
  .bc-header__link { font-size: var(--text-small); font-weight: var(--weight-medium); color: var(--color-heading); padding: 0.5rem 0; }
  .bc-header__link[aria-current="page"] { color: var(--color-link-hover); }
  .bc-header__menu { display: none; align-items: center; justify-content: center; width: 48px; height: 48px; background: none; border: none; cursor: pointer; color: var(--color-heading); font-size: 22px; }
  @media (max-width: 820px) {
    .bc-header__links, .bc-header__nav .bc-btn { display: none; }
    .bc-header__menu { display: inline-flex; }
  }
  `;
  const el = document.createElement('style');
  el.setAttribute('data-bc', 'header');
  el.textContent = css;
  document.head.appendChild(el);
}

/**
 * Site Header — the backchain.ai top bar: brand lockup left, nav links and a
 * single primary CTA right, hamburger below 820px. Composes <Button>.
 */
function SiteHeader({
  logoSrc,
  logoAlt = 'Backchain',
  brandHref = '#',
  links = [],
  cta = {
    label: "Let's talk",
    href: '#contact'
  },
  onMenuToggle,
  className = '',
  ...rest
}) {
  useHeaderStyles();
  return /*#__PURE__*/React.createElement("header", _extends({
    className: `bc-header ${className}`.trim()
  }, rest), /*#__PURE__*/React.createElement("div", {
    className: "bc-header__inner"
  }, /*#__PURE__*/React.createElement("a", {
    className: "bc-header__brand no-underline",
    href: brandHref,
    "aria-label": logoAlt
  }, logoSrc ? /*#__PURE__*/React.createElement("img", {
    src: logoSrc,
    alt: logoAlt
  }) : /*#__PURE__*/React.createElement("span", {
    className: "bc-header__wordmark"
  }, "Backchain")), /*#__PURE__*/React.createElement("nav", {
    className: "bc-header__nav",
    "aria-label": "Primary"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-header__links"
  }, links.map((l, i) => /*#__PURE__*/React.createElement("a", {
    key: i,
    className: "bc-header__link no-underline",
    href: l.href,
    "aria-current": l.current ? 'page' : undefined
  }, l.label))), cta ? /*#__PURE__*/React.createElement(__ds_scope.Button, {
    href: cta.href,
    size: "sm"
  }, cta.label) : null, /*#__PURE__*/React.createElement("button", {
    className: "bc-header__menu",
    "aria-label": "Open menu",
    "aria-expanded": "false",
    onClick: onMenuToggle
  }, "\u2261"))));
}
Object.assign(__ds_scope, { SiteHeader });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/SiteHeader.jsx", error: String((e && e.message) || e) }); }

// source/tokens/tailwind_preset.mjs
try { (() => {
/**
 * Tailwind preset — Chris Krough + Backchain design tokens
 *
 * Usage in a consumer Tailwind config:
 *
 *   import brandPreset from '../path/to/brand/visual-identity/tailwind_preset.mjs';
 *
 *   export default {
 *     presets: [brandPreset],
 *     content: ['./src/**\/*.{astro,html,js,jsx,ts,tsx,md,mdx}'],
 *   };
 *
 * Colors support Tailwind's `<color>/<opacity>` syntax natively
 * (e.g. `border-gray/10`, `text-cream/80`). No extra config needed.
 *
 * Authoritative source: brand/visual-identity/design_tokens.json
 */
/** @type {import('tailwindcss').Config} */
try {
  void {
    theme: {
      extend: {
        colors: {
          // Shared palette
          cream: '#F5F0E8',
          slate: '#2F455B',
          charcoal: '#41423D',
          coral: '#E07A5F',
          'coral-deep': '#A35945',
          'off-white': '#FAFAF8',
          gray: '#50636F',
          // Status
          error: '#C0392B',
          success: '#27AE60'
        },
        fontFamily: {
          brand: ['Outfit', 'system-ui', 'sans-serif'],
          content: ['Inter', 'system-ui', 'sans-serif'],
          mono: ['JetBrains Mono', 'monospace']
        },
        fontSize: {
          // Fluid type — clamp(min, preferred, max)
          display: ['clamp(2.25rem, 1.5rem + 3.75vw, 3.75rem)', {
            lineHeight: '1.1'
          }],
          h1: ['clamp(1.875rem, 1.5rem + 1.875vw, 2.25rem)', {
            lineHeight: '1.2'
          }],
          h2: ['clamp(1.5rem, 1.25rem + 1.25vw, 2rem)', {
            lineHeight: '1.25'
          }],
          h3: ['clamp(1.25rem, 1.125rem + 0.625vw, 1.5rem)', {
            lineHeight: '1.3'
          }],
          h4: ['clamp(1.125rem, 1.0625rem + 0.3125vw, 1.25rem)', {
            lineHeight: '1.4'
          }]
        },
        spacing: {
          // Design-token spacing scale (suffix tokens alongside Tailwind defaults)
          'space-xs': '0.5rem',
          'space-sm': '1rem',
          'space-md': '1.5rem',
          'space-lg': '2rem',
          'space-xl': '3rem',
          'space-2xl': '4rem',
          'space-3xl': '6rem'
        },
        maxWidth: {
          content: '65ch',
          layout: '72rem' // 1152px — page container
        },
        height: {
          'header-sm': '6rem',
          'header-lg': '7rem'
        },
        minHeight: {
          touch: '48px'
        },
        borderRadius: {
          // Tailwind's default `rounded` (4px) = --radius-md
          // Tailwind's default `rounded-lg` (8px) = --radius-lg
          // Add explicit aliases for clarity.
          'radius-sm': '2px',
          'radius-md': '4px',
          'radius-lg': '8px',
          pill: '9999px'
        },
        boxShadow: {
          'elevation-sm': '0 1px 2px rgba(47, 69, 91, 0.06)',
          'elevation-md': '0 2px 8px rgba(47, 69, 91, 0.08), 0 1px 2px rgba(47, 69, 91, 0.04)',
          'elevation-lg': '0 8px 24px rgba(47, 69, 91, 0.10), 0 2px 6px rgba(47, 69, 91, 0.06)',
          'elevation-xl': '0 16px 48px rgba(47, 69, 91, 0.14), 0 4px 12px rgba(47, 69, 91, 0.08)'
        },
        transitionDuration: {
          fast: '150ms',
          default: '200ms',
          slow: '300ms',
          xslow: '400ms'
        },
        transitionTimingFunction: {
          'brand-out': 'cubic-bezier(0.16, 1, 0.3, 1)',
          'brand-in-out': 'cubic-bezier(0.4, 0, 0.2, 1)'
        },
        zIndex: {
          base: '0',
          raised: '10',
          dropdown: '100',
          sticky: '200',
          overlay: '1000',
          modal: '1100',
          toast: '1200',
          tooltip: '1300'
        },
        letterSpacing: {
          'brand-tight': '-0.02em',
          'brand-wide': '0.05em'
        }
      }
    }
  };
} catch {}
})(); } catch (e) { __ds_ns.__errors.push({ path: "source/tokens/tailwind_preset.mjs", error: String((e && e.message) || e) }); }

// ui_kits/backchain-website/Approach.jsx
try { (() => {
/* Backchain website — Approach section on a dark slate band. The backchaining method. */
function Approach() {
  const {
    SectionLabel,
    StyledList
  } = window.BackchainDesignSystem_498b67;
  const steps = [{
    n: '01',
    t: 'Start with the outcome',
    d: 'Name the business result you want, in plain terms. Not "adopt AI" — "cut quote turnaround from three days to one."'
  }, {
    n: '02',
    t: 'Map the chain backward',
    d: 'Work back from that outcome to the capabilities, data, and processes each step depends on. The chain is built last-step-first.'
  }, {
    n: '03',
    t: 'Prototype the riskiest link',
    d: 'Build a litmus test for the step most likely to fail. Fail fast and cheap, before any major investment.'
  }, {
    n: '04',
    t: 'Ship, measure, expand',
    d: 'Put the working link into real use, measure it honestly, then add the next step. Returns compound as the chain grows.'
  }];
  return /*#__PURE__*/React.createElement("section", {
    className: "bc-section bc-approach on-slate",
    id: "approach"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-container"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-approach__grid"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-approach__intro"
  }, /*#__PURE__*/React.createElement(SectionLabel, null, "The method"), /*#__PURE__*/React.createElement("h2", {
    className: "bc-section__title"
  }, "We work backward", /*#__PURE__*/React.createElement("br", null), "from the outcome."), /*#__PURE__*/React.createElement("p", {
    className: "bc-section__lead"
  }, "Backchain is named for backchain training: you master the final step first, then build the chain backward so the learner always knows where it is going. The consulting works the same way."), /*#__PURE__*/React.createElement(StyledList, {
    items: ['Fail-fast prototypes before major investment', 'Honest assessment, including when AI is not the answer', 'Solutions that scale with increasing returns over time']
  })), /*#__PURE__*/React.createElement("ol", {
    className: "bc-steps"
  }, steps.map(s => /*#__PURE__*/React.createElement("li", {
    key: s.n,
    className: "bc-step"
  }, /*#__PURE__*/React.createElement("span", {
    className: "bc-step__n"
  }, s.n), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", {
    className: "bc-step__t"
  }, s.t), /*#__PURE__*/React.createElement("p", {
    className: "bc-step__d"
  }, s.d))))))));
}
window.Approach = Approach;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/backchain-website/Approach.jsx", error: String((e && e.message) || e) }); }

// ui_kits/backchain-website/Contact.jsx
try { (() => {
/* Backchain website — Contact section with a working (fake) form. */
function Contact() {
  const {
    TextField,
    Button,
    SectionLabel,
    Card
  } = window.BackchainDesignSystem_498b67;
  const [sent, setSent] = React.useState(false);
  const [errors, setErrors] = React.useState({});
  function submit(e) {
    e.preventDefault();
    const data = new FormData(e.target);
    const next = {};
    if (!data.get('name')) next.name = 'Please add your name.';
    const email = (data.get('email') || '').toString();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) next.email = 'Please enter a valid email address.';
    if (!data.get('message')) next.message = 'A sentence or two is plenty.';
    setErrors(next);
    if (Object.keys(next).length === 0) setSent(true);
  }
  return /*#__PURE__*/React.createElement("section", {
    className: "bc-section bc-contact",
    id: "contact"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-container bc-contact__grid"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-contact__intro"
  }, /*#__PURE__*/React.createElement(SectionLabel, null, "Start a conversation"), /*#__PURE__*/React.createElement("h2", {
    className: "bc-section__title"
  }, "Tell me the workflow that", /*#__PURE__*/React.createElement("br", null), "eats the most time."), /*#__PURE__*/React.createElement("p", {
    className: "bc-section__lead"
  }, "The costliest workflow is usually the one nobody named in the kickoff, because people stopped noticing they were doing it by hand. That is the one worth a look."), /*#__PURE__*/React.createElement("dl", {
    className: "bc-terms"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("dt", null, "Rate"), /*#__PURE__*/React.createElement("dd", null, "$270/hr, prepaid retainer, unused balance refunded at delivery.")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("dt", null, "Availability"), /*#__PURE__*/React.createElement("dd", null, "Monday\u2013Wednesday, 20-hour weekly cap. One open slot in the near pipeline.")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("dt", null, "Direct"), /*#__PURE__*/React.createElement("dd", null, /*#__PURE__*/React.createElement("a", {
    href: "mailto:chris@backchain.ai"
  }, "chris@backchain.ai"))))), /*#__PURE__*/React.createElement(Card, {
    padding: "lg",
    className: "bc-contact__card"
  }, sent ? /*#__PURE__*/React.createElement("div", {
    className: "bc-sent",
    role: "status"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-sent__mark",
    "aria-hidden": "true"
  }, "\u2713"), /*#__PURE__*/React.createElement("h3", {
    className: "bc-service__title"
  }, "Message sent"), /*#__PURE__*/React.createElement("p", {
    className: "bc-service__body"
  }, "I respond within one business day, usually with a question or two before any call.")) : /*#__PURE__*/React.createElement("form", {
    onSubmit: submit,
    noValidate: true
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-form__row"
  }, /*#__PURE__*/React.createElement(TextField, {
    label: "Name",
    name: "name",
    required: true,
    placeholder: "Jane Rivera",
    error: errors.name
  }), /*#__PURE__*/React.createElement(TextField, {
    label: "Email",
    name: "email",
    type: "email",
    required: true,
    placeholder: "jane@example.com",
    error: errors.email
  })), /*#__PURE__*/React.createElement(TextField, {
    label: "Company",
    name: "company",
    placeholder: "Acme Co.",
    hint: "Optional \u2014 helps me tailor the call."
  }), /*#__PURE__*/React.createElement(TextField, {
    label: "What's the workflow?",
    name: "message",
    multiline: true,
    required: true,
    placeholder: "Tell me about the task and roughly how much senior-staff time it takes each week.",
    error: errors.message
  }), /*#__PURE__*/React.createElement(Button, {
    type: "submit",
    size: "lg",
    className: "bc-form__submit"
  }, "Send message")))));
}
window.Contact = Contact;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/backchain-website/Contact.jsx", error: String((e && e.message) || e) }); }

// ui_kits/backchain-website/Hero.jsx
try { (() => {
/* Backchain website — Hero section. Composes SiteHeader, Button, StatGrid, SectionLabel. */
function Hero() {
  const {
    Button,
    StatGrid,
    SectionLabel
  } = window.BackchainDesignSystem_498b67;
  return /*#__PURE__*/React.createElement("section", {
    className: "bc-hero",
    id: "top"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-hero__inner"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-hero__copy"
  }, /*#__PURE__*/React.createElement(SectionLabel, null, "AI & automation consulting"), /*#__PURE__*/React.createElement("h1", {
    className: "bc-hero__title"
  }, "Discover where AI works,", /*#__PURE__*/React.createElement("br", null), "and where it doesn't."), /*#__PURE__*/React.createElement("p", {
    className: "bc-hero__sub"
  }, "Twenty-five years scaling platforms through 3 IPOs, 8 acquisitions, and 6,700% growth. Now helping small and mid-sized teams automate what matters, and skip what doesn't."), /*#__PURE__*/React.createElement("div", {
    className: "bc-hero__cta"
  }, /*#__PURE__*/React.createElement(Button, {
    href: "#contact",
    size: "lg"
  }, "Book a discovery call"), /*#__PURE__*/React.createElement(Button, {
    href: "#approach",
    size: "lg",
    variant: "secondary"
  }, "See the approach"))), /*#__PURE__*/React.createElement("div", {
    className: "bc-hero__proof"
  }, /*#__PURE__*/React.createElement(StatGrid, {
    columns: 2,
    stats: [{
      value: '6,700%',
      label: 'revenue growth supported at OJO'
    }, {
      value: '$3B',
      label: 'in transactions on platforms run'
    }, {
      value: '99.99%',
      label: 'uptime across multiple companies'
    }, {
      value: '200+',
      label: 'services migrated, zero downtime'
    }]
  }))));
}
window.Hero = Hero;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/backchain-website/Hero.jsx", error: String((e && e.message) || e) }); }

// ui_kits/backchain-website/Services.jsx
try { (() => {
/* Backchain website — Services section. Three flat cards. */
function Services() {
  const {
    Card,
    SectionLabel,
    Button,
    Badge
  } = window.BackchainDesignSystem_498b67;
  const services = [{
    eyebrow: 'Phase 01',
    title: 'AI Readiness Assessment',
    body: 'A clear-eyed evaluation of your data, processes, and people before anyone writes code. You leave knowing where automation pays, and where it would just burn budget.',
    cta: 'What it covers',
    badge: 'Start here'
  }, {
    eyebrow: 'Phase 02',
    title: 'Process Automation',
    body: 'Find the workflow quietly eating the most senior-staff time and ship a litmus-test prototype in week one. Prove value on a real task before any major investment.',
    cta: 'How it works'
  }, {
    eyebrow: 'Phase 03',
    title: 'Fractional AI Leadership',
    body: 'Embedded, part-time engineering leadership for the AI-era decisions you cannot yet hire for. Strong opinions, thought out loud with your team, not lectured at them.',
    cta: 'See engagements'
  }];
  return /*#__PURE__*/React.createElement("section", {
    className: "bc-section",
    id: "services"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-container"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-section__head"
  }, /*#__PURE__*/React.createElement(SectionLabel, null, "Services"), /*#__PURE__*/React.createElement("h2", {
    className: "bc-section__title"
  }, "Three ways to start, all outcome-first"), /*#__PURE__*/React.createElement("p", {
    className: "bc-section__lead"
  }, "Every engagement begins with the result you want, then works backward to the capabilities and data that get you there. No implement-first, ask-questions-later.")), /*#__PURE__*/React.createElement("div", {
    className: "bc-services__grid"
  }, services.map((s, i) => /*#__PURE__*/React.createElement(Card, {
    key: i,
    interactive: true,
    padding: "lg",
    className: "bc-service"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bc-service__top"
  }, /*#__PURE__*/React.createElement(SectionLabel, null, s.eyebrow), s.badge ? /*#__PURE__*/React.createElement(Badge, {
    variant: "accent"
  }, s.badge) : null), /*#__PURE__*/React.createElement("h3", {
    className: "bc-service__title"
  }, s.title), /*#__PURE__*/React.createElement("p", {
    className: "bc-service__body"
  }, s.body), /*#__PURE__*/React.createElement(Button, {
    variant: "tertiary",
    iconRight: "\u2192"
  }, s.cta))))));
}
window.Services = Services;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/backchain-website/Services.jsx", error: String((e && e.message) || e) }); }

// ui_kits/backchain-website/tweaks-panel.jsx
try { (() => {
// @ds-adherence-ignore -- omelette starter scaffold (raw elements/hex/px by design)

/* BEGIN USAGE */
// tweaks-panel.jsx
// Reusable Tweaks shell + form-control helpers.
// Exports (to window): useTweaks, TweaksPanel, TweakSection, TweakRow, TweakSlider,
//   TweakToggle, TweakRadio, TweakSelect, TweakText, TweakNumber, TweakColor, TweakButton.
//
// Owns the host protocol (listens for __activate_edit_mode / __deactivate_edit_mode,
// posts __edit_mode_available / __edit_mode_set_keys / __edit_mode_dismissed) so
// individual prototypes don't re-roll it. Ships a consistent set of controls so you
// don't hand-draw <input type="range">, segmented radios, steppers, etc.
//
// Usage (in an HTML file that loads React + Babel):
//
//   const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
//     "primaryColor": "#D97757",
//     "palette": ["#D97757", "#29261b", "#f6f4ef"],
//     "fontSize": 16,
//     "density": "regular",
//     "dark": false
//   }/*EDITMODE-END*/;
//
//   function App() {
//     const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
//     return (
//       <div style={{ fontSize: t.fontSize, color: t.primaryColor }}>
//         Hello
//         <TweaksPanel>
//           <TweakSection label="Typography" />
//           <TweakSlider label="Font size" value={t.fontSize} min={10} max={32} unit="px"
//                        onChange={(v) => setTweak('fontSize', v)} />
//           <TweakRadio  label="Density" value={t.density}
//                        options={['compact', 'regular', 'comfy']}
//                        onChange={(v) => setTweak('density', v)} />
//           <TweakSection label="Theme" />
//           <TweakColor  label="Primary" value={t.primaryColor}
//                        options={['#D97757', '#2A6FDB', '#1F8A5B', '#7A5AE0']}
//                        onChange={(v) => setTweak('primaryColor', v)} />
//           <TweakColor  label="Palette" value={t.palette}
//                        options={[['#D97757', '#29261b', '#f6f4ef'],
//                                  ['#475569', '#0f172a', '#f1f5f9']]}
//                        onChange={(v) => setTweak('palette', v)} />
//           <TweakToggle label="Dark mode" value={t.dark}
//                        onChange={(v) => setTweak('dark', v)} />
//         </TweaksPanel>
//       </div>
//     );
//   }
//
// TweakRadio is the segmented control for 2–3 short options (auto-falls-back to
// TweakSelect past ~16/~10 chars per label); reach for TweakSelect directly when
// options are many or long. For color tweaks always curate 3-4 options rather than
// a free picker; an option can also be a whole 2–5 color palette (the stored value
// is the array). The Tweak* controls are a floor, not a ceiling — build custom
// controls inside the panel if a tweak calls for UI they don't cover.
/* END USAGE */
// ─────────────────────────────────────────────────────────────────────────────

const __TWEAKS_STYLE = `
  .twk-panel{position:fixed;right:16px;bottom:16px;z-index:2147483646;width:280px;
    max-height:calc(100vh - 32px);display:flex;flex-direction:column;
    transform:scale(var(--dc-inv-zoom,1));transform-origin:bottom right;
    background:rgba(250,249,247,.78);color:#29261b;
    -webkit-backdrop-filter:blur(24px) saturate(160%);backdrop-filter:blur(24px) saturate(160%);
    border:.5px solid rgba(255,255,255,.6);border-radius:14px;
    box-shadow:0 1px 0 rgba(255,255,255,.5) inset,0 12px 40px rgba(0,0,0,.18);
    font:11.5px/1.4 ui-sans-serif,system-ui,-apple-system,sans-serif;overflow:hidden}
  .twk-hd{display:flex;align-items:center;justify-content:space-between;
    padding:10px 8px 10px 14px;cursor:move;user-select:none}
  .twk-hd b{font-size:12px;font-weight:600;letter-spacing:.01em}
  .twk-x{appearance:none;border:0;background:transparent;color:rgba(41,38,27,.55);
    width:22px;height:22px;border-radius:6px;cursor:default;font-size:13px;line-height:1}
  .twk-x:hover{background:rgba(0,0,0,.06);color:#29261b}
  .twk-body{padding:2px 14px 14px;display:flex;flex-direction:column;gap:10px;
    overflow-y:auto;overflow-x:hidden;min-height:0;
    scrollbar-width:thin;scrollbar-color:rgba(0,0,0,.15) transparent}
  .twk-body::-webkit-scrollbar{width:8px}
  .twk-body::-webkit-scrollbar-track{background:transparent;margin:2px}
  .twk-body::-webkit-scrollbar-thumb{background:rgba(0,0,0,.15);border-radius:4px;
    border:2px solid transparent;background-clip:content-box}
  .twk-body::-webkit-scrollbar-thumb:hover{background:rgba(0,0,0,.25);
    border:2px solid transparent;background-clip:content-box}
  .twk-row{display:flex;flex-direction:column;gap:5px}
  .twk-row-h{flex-direction:row;align-items:center;justify-content:space-between;gap:10px}
  .twk-lbl{display:flex;justify-content:space-between;align-items:baseline;
    color:rgba(41,38,27,.72)}
  .twk-lbl>span:first-child{font-weight:500}
  .twk-val{color:rgba(41,38,27,.5);font-variant-numeric:tabular-nums}

  .twk-sect{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
    color:rgba(41,38,27,.45);padding:10px 0 0}
  .twk-sect:first-child{padding-top:0}

  .twk-field{appearance:none;box-sizing:border-box;width:100%;min-width:0;height:26px;padding:0 8px;
    border:.5px solid rgba(0,0,0,.1);border-radius:7px;
    background:rgba(255,255,255,.6);color:inherit;font:inherit;outline:none}
  .twk-field:focus{border-color:rgba(0,0,0,.25);background:rgba(255,255,255,.85)}
  select.twk-field{padding-right:22px;
    background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path fill='rgba(0,0,0,.5)' d='M0 0h10L5 6z'/></svg>");
    background-repeat:no-repeat;background-position:right 8px center}

  .twk-slider{appearance:none;-webkit-appearance:none;width:100%;height:4px;margin:6px 0;
    border-radius:999px;background:rgba(0,0,0,.12);outline:none}
  .twk-slider::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;
    width:14px;height:14px;border-radius:50%;background:#fff;
    border:.5px solid rgba(0,0,0,.12);box-shadow:0 1px 3px rgba(0,0,0,.2);cursor:default}
  .twk-slider::-moz-range-thumb{width:14px;height:14px;border-radius:50%;
    background:#fff;border:.5px solid rgba(0,0,0,.12);box-shadow:0 1px 3px rgba(0,0,0,.2);cursor:default}

  .twk-seg{position:relative;display:flex;padding:2px;border-radius:8px;
    background:rgba(0,0,0,.06);user-select:none}
  .twk-seg-thumb{position:absolute;top:2px;bottom:2px;border-radius:6px;
    background:rgba(255,255,255,.9);box-shadow:0 1px 2px rgba(0,0,0,.12);
    transition:left .15s cubic-bezier(.3,.7,.4,1),width .15s}
  .twk-seg.dragging .twk-seg-thumb{transition:none}
  .twk-seg button{appearance:none;position:relative;z-index:1;flex:1;border:0;
    background:transparent;color:inherit;font:inherit;font-weight:500;min-height:22px;
    border-radius:6px;cursor:default;padding:4px 6px;line-height:1.2;
    overflow-wrap:anywhere}

  .twk-toggle{position:relative;width:32px;height:18px;border:0;border-radius:999px;
    background:rgba(0,0,0,.15);transition:background .15s;cursor:default;padding:0}
  .twk-toggle[data-on="1"]{background:#34c759}
  .twk-toggle i{position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;
    background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.25);transition:transform .15s}
  .twk-toggle[data-on="1"] i{transform:translateX(14px)}

  .twk-num{display:flex;align-items:center;box-sizing:border-box;min-width:0;height:26px;padding:0 0 0 8px;
    border:.5px solid rgba(0,0,0,.1);border-radius:7px;background:rgba(255,255,255,.6)}
  .twk-num-lbl{font-weight:500;color:rgba(41,38,27,.6);cursor:ew-resize;
    user-select:none;padding-right:8px}
  .twk-num input{flex:1;min-width:0;height:100%;border:0;background:transparent;
    font:inherit;font-variant-numeric:tabular-nums;text-align:right;padding:0 8px 0 0;
    outline:none;color:inherit;-moz-appearance:textfield}
  .twk-num input::-webkit-inner-spin-button,.twk-num input::-webkit-outer-spin-button{
    -webkit-appearance:none;margin:0}
  .twk-num-unit{padding-right:8px;color:rgba(41,38,27,.45)}

  .twk-btn{appearance:none;height:26px;padding:0 12px;border:0;border-radius:7px;
    background:rgba(0,0,0,.78);color:#fff;font:inherit;font-weight:500;cursor:default}
  .twk-btn:hover{background:rgba(0,0,0,.88)}
  .twk-btn.secondary{background:rgba(0,0,0,.06);color:inherit}
  .twk-btn.secondary:hover{background:rgba(0,0,0,.1)}

  .twk-swatch{appearance:none;-webkit-appearance:none;width:56px;height:22px;
    border:.5px solid rgba(0,0,0,.1);border-radius:6px;padding:0;cursor:default;
    background:transparent;flex-shrink:0}
  .twk-swatch::-webkit-color-swatch-wrapper{padding:0}
  .twk-swatch::-webkit-color-swatch{border:0;border-radius:5.5px}
  .twk-swatch::-moz-color-swatch{border:0;border-radius:5.5px}

  .twk-chips{display:flex;gap:6px}
  .twk-chip{position:relative;appearance:none;flex:1;min-width:0;height:46px;
    padding:0;border:0;border-radius:6px;overflow:hidden;cursor:default;
    box-shadow:0 0 0 .5px rgba(0,0,0,.12),0 1px 2px rgba(0,0,0,.06);
    transition:transform .12s cubic-bezier(.3,.7,.4,1),box-shadow .12s}
  .twk-chip:hover{transform:translateY(-1px);
    box-shadow:0 0 0 .5px rgba(0,0,0,.18),0 4px 10px rgba(0,0,0,.12)}
  .twk-chip[data-on="1"]{box-shadow:0 0 0 1.5px rgba(0,0,0,.85),
    0 2px 6px rgba(0,0,0,.15)}
  .twk-chip>span{position:absolute;top:0;bottom:0;right:0;width:34%;
    display:flex;flex-direction:column;box-shadow:-1px 0 0 rgba(0,0,0,.1)}
  .twk-chip>span>i{flex:1;box-shadow:0 -1px 0 rgba(0,0,0,.1)}
  .twk-chip>span>i:first-child{box-shadow:none}
  .twk-chip svg{position:absolute;top:6px;left:6px;width:13px;height:13px;
    filter:drop-shadow(0 1px 1px rgba(0,0,0,.3))}
`;

// ── useTweaks ───────────────────────────────────────────────────────────────
// Single source of truth for tweak values. setTweak persists via the host
// (__edit_mode_set_keys → host rewrites the EDITMODE block on disk).
function useTweaks(defaults) {
  const [values, setValues] = React.useState(defaults);
  // Accepts either setTweak('key', value) or setTweak({ key: value, ... }) so a
  // useState-style call doesn't write a "[object Object]" key into the persisted
  // JSON block.
  const setTweak = React.useCallback((keyOrEdits, val) => {
    const edits = typeof keyOrEdits === 'object' && keyOrEdits !== null ? keyOrEdits : {
      [keyOrEdits]: val
    };
    setValues(prev => ({
      ...prev,
      ...edits
    }));
    window.parent.postMessage({
      type: '__edit_mode_set_keys',
      edits
    }, '*');
    // Same-window signal so in-page listeners (deck-stage rail thumbnails)
    // can react — the parent message only reaches the host, not peers.
    window.dispatchEvent(new CustomEvent('tweakchange', {
      detail: edits
    }));
  }, []);
  return [values, setTweak];
}

// ── TweaksPanel ─────────────────────────────────────────────────────────────
// Floating shell. Registers the protocol listener BEFORE announcing
// availability — if the announce ran first, the host's activate could land
// before our handler exists and the toolbar toggle would silently no-op.
// The close button posts __edit_mode_dismissed so the host's toolbar toggle
// flips off in lockstep; the host echoes __deactivate_edit_mode back which
// is what actually hides the panel.
function TweaksPanel({
  title = 'Tweaks',
  children
}) {
  const [open, setOpen] = React.useState(false);
  const dragRef = React.useRef(null);
  const offsetRef = React.useRef({
    x: 16,
    y: 16
  });
  const PAD = 16;
  const clampToViewport = React.useCallback(() => {
    const panel = dragRef.current;
    if (!panel) return;
    const w = panel.offsetWidth,
      h = panel.offsetHeight;
    const maxRight = Math.max(PAD, window.innerWidth - w - PAD);
    const maxBottom = Math.max(PAD, window.innerHeight - h - PAD);
    offsetRef.current = {
      x: Math.min(maxRight, Math.max(PAD, offsetRef.current.x)),
      y: Math.min(maxBottom, Math.max(PAD, offsetRef.current.y))
    };
    panel.style.right = offsetRef.current.x + 'px';
    panel.style.bottom = offsetRef.current.y + 'px';
  }, []);
  React.useEffect(() => {
    if (!open) return;
    clampToViewport();
    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', clampToViewport);
      return () => window.removeEventListener('resize', clampToViewport);
    }
    const ro = new ResizeObserver(clampToViewport);
    ro.observe(document.documentElement);
    return () => ro.disconnect();
  }, [open, clampToViewport]);
  React.useEffect(() => {
    const onMsg = e => {
      const t = e?.data?.type;
      if (t === '__activate_edit_mode') setOpen(true);else if (t === '__deactivate_edit_mode') setOpen(false);
    };
    window.addEventListener('message', onMsg);
    window.parent.postMessage({
      type: '__edit_mode_available'
    }, '*');
    return () => window.removeEventListener('message', onMsg);
  }, []);
  const dismiss = () => {
    setOpen(false);
    window.parent.postMessage({
      type: '__edit_mode_dismissed'
    }, '*');
  };
  const onDragStart = e => {
    const panel = dragRef.current;
    if (!panel) return;
    const r = panel.getBoundingClientRect();
    const sx = e.clientX,
      sy = e.clientY;
    const startRight = window.innerWidth - r.right;
    const startBottom = window.innerHeight - r.bottom;
    const move = ev => {
      offsetRef.current = {
        x: startRight - (ev.clientX - sx),
        y: startBottom - (ev.clientY - sy)
      };
      clampToViewport();
    };
    const up = () => {
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', up);
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
  };
  if (!open) return null;
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("style", null, __TWEAKS_STYLE), /*#__PURE__*/React.createElement("div", {
    ref: dragRef,
    className: "twk-panel",
    "data-omelette-chrome": "",
    style: {
      right: offsetRef.current.x,
      bottom: offsetRef.current.y
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-hd",
    onMouseDown: onDragStart
  }, /*#__PURE__*/React.createElement("b", null, title), /*#__PURE__*/React.createElement("button", {
    className: "twk-x",
    "aria-label": "Close tweaks",
    onMouseDown: e => e.stopPropagation(),
    onClick: dismiss
  }, "\u2715")), /*#__PURE__*/React.createElement("div", {
    className: "twk-body"
  }, children)));
}

// ── Layout helpers ──────────────────────────────────────────────────────────

function TweakSection({
  label,
  children
}) {
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "twk-sect"
  }, label), children);
}
function TweakRow({
  label,
  value,
  children,
  inline = false
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: inline ? 'twk-row twk-row-h' : 'twk-row'
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-lbl"
  }, /*#__PURE__*/React.createElement("span", null, label), value != null && /*#__PURE__*/React.createElement("span", {
    className: "twk-val"
  }, value)), children);
}

// ── Controls ────────────────────────────────────────────────────────────────

function TweakSlider({
  label,
  value,
  min = 0,
  max = 100,
  step = 1,
  unit = '',
  onChange
}) {
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label,
    value: `${value}${unit}`
  }, /*#__PURE__*/React.createElement("input", {
    type: "range",
    className: "twk-slider",
    min: min,
    max: max,
    step: step,
    value: value,
    onChange: e => onChange(Number(e.target.value))
  }));
}
function TweakToggle({
  label,
  value,
  onChange
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "twk-row twk-row-h"
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-lbl"
  }, /*#__PURE__*/React.createElement("span", null, label)), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "twk-toggle",
    "data-on": value ? '1' : '0',
    role: "switch",
    "aria-checked": !!value,
    onClick: () => onChange(!value)
  }, /*#__PURE__*/React.createElement("i", null)));
}
function TweakRadio({
  label,
  value,
  options,
  onChange
}) {
  const trackRef = React.useRef(null);
  const [dragging, setDragging] = React.useState(false);
  // The active value is read by pointer-move handlers attached for the lifetime
  // of a drag — ref it so a stale closure doesn't fire onChange for every move.
  const valueRef = React.useRef(value);
  valueRef.current = value;

  // Segments wrap mid-word once per-segment width runs out. The track is
  // ~248px (280 panel − 28 body pad − 4 seg pad), each button loses 12px
  // to its own padding, and 11.5px system-ui averages ~6.3px/char — so 2
  // options fit ~16 chars each, 3 fit ~10. Past that (or >3 options), fall
  // back to a dropdown rather than wrap.
  const labelLen = o => String(typeof o === 'object' ? o.label : o).length;
  const maxLen = options.reduce((m, o) => Math.max(m, labelLen(o)), 0);
  const fitsAsSegments = maxLen <= ({
    2: 16,
    3: 10
  }[options.length] ?? 0);
  if (!fitsAsSegments) {
    // <select> emits strings — map back to the original option value so the
    // fallback stays type-preserving (numbers, booleans) like the segment path.
    const resolve = s => {
      const m = options.find(o => String(typeof o === 'object' ? o.value : o) === s);
      return m === undefined ? s : typeof m === 'object' ? m.value : m;
    };
    return /*#__PURE__*/React.createElement(TweakSelect, {
      label: label,
      value: value,
      options: options,
      onChange: s => onChange(resolve(s))
    });
  }
  const opts = options.map(o => typeof o === 'object' ? o : {
    value: o,
    label: o
  });
  const idx = Math.max(0, opts.findIndex(o => o.value === value));
  const n = opts.length;
  const segAt = clientX => {
    const r = trackRef.current.getBoundingClientRect();
    const inner = r.width - 4;
    const i = Math.floor((clientX - r.left - 2) / inner * n);
    return opts[Math.max(0, Math.min(n - 1, i))].value;
  };
  const onPointerDown = e => {
    setDragging(true);
    const v0 = segAt(e.clientX);
    if (v0 !== valueRef.current) onChange(v0);
    const move = ev => {
      if (!trackRef.current) return;
      const v = segAt(ev.clientX);
      if (v !== valueRef.current) onChange(v);
    };
    const up = () => {
      setDragging(false);
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("div", {
    ref: trackRef,
    role: "radiogroup",
    onPointerDown: onPointerDown,
    className: dragging ? 'twk-seg dragging' : 'twk-seg'
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-seg-thumb",
    style: {
      left: `calc(2px + ${idx} * (100% - 4px) / ${n})`,
      width: `calc((100% - 4px) / ${n})`
    }
  }), opts.map(o => /*#__PURE__*/React.createElement("button", {
    key: o.value,
    type: "button",
    role: "radio",
    "aria-checked": o.value === value
  }, o.label))));
}
function TweakSelect({
  label,
  value,
  options,
  onChange
}) {
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("select", {
    className: "twk-field",
    value: value,
    onChange: e => onChange(e.target.value)
  }, options.map(o => {
    const v = typeof o === 'object' ? o.value : o;
    const l = typeof o === 'object' ? o.label : o;
    return /*#__PURE__*/React.createElement("option", {
      key: v,
      value: v
    }, l);
  })));
}
function TweakText({
  label,
  value,
  placeholder,
  onChange
}) {
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("input", {
    className: "twk-field",
    type: "text",
    value: value,
    placeholder: placeholder,
    onChange: e => onChange(e.target.value)
  }));
}
function TweakNumber({
  label,
  value,
  min,
  max,
  step = 1,
  unit = '',
  onChange
}) {
  const clamp = n => {
    if (min != null && n < min) return min;
    if (max != null && n > max) return max;
    return n;
  };
  const startRef = React.useRef({
    x: 0,
    val: 0
  });
  const onScrubStart = e => {
    e.preventDefault();
    startRef.current = {
      x: e.clientX,
      val: value
    };
    const decimals = (String(step).split('.')[1] || '').length;
    const move = ev => {
      const dx = ev.clientX - startRef.current.x;
      const raw = startRef.current.val + dx * step;
      const snapped = Math.round(raw / step) * step;
      onChange(clamp(Number(snapped.toFixed(decimals))));
    };
    const up = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "twk-num"
  }, /*#__PURE__*/React.createElement("span", {
    className: "twk-num-lbl",
    onPointerDown: onScrubStart
  }, label), /*#__PURE__*/React.createElement("input", {
    type: "number",
    value: value,
    min: min,
    max: max,
    step: step,
    onChange: e => onChange(clamp(Number(e.target.value)))
  }), unit && /*#__PURE__*/React.createElement("span", {
    className: "twk-num-unit"
  }, unit));
}

// Relative-luminance contrast pick — checkmarks drawn over a swatch need to
// read on both #111 and #fafafa without per-option configuration. Hex input
// only (#rgb / #rrggbb); named or rgb()/hsl() colors fall through to "light".
function __twkIsLight(hex) {
  const h = String(hex).replace('#', '');
  const x = h.length === 3 ? h.replace(/./g, c => c + c) : h.padEnd(6, '0');
  const n = parseInt(x.slice(0, 6), 16);
  if (Number.isNaN(n)) return true;
  const r = n >> 16 & 255,
    g = n >> 8 & 255,
    b = n & 255;
  return r * 299 + g * 587 + b * 114 > 148000;
}
const __TwkCheck = ({
  light
}) => /*#__PURE__*/React.createElement("svg", {
  viewBox: "0 0 14 14",
  "aria-hidden": "true"
}, /*#__PURE__*/React.createElement("path", {
  d: "M3 7.2 5.8 10 11 4.2",
  fill: "none",
  strokeWidth: "2.2",
  strokeLinecap: "round",
  strokeLinejoin: "round",
  stroke: light ? 'rgba(0,0,0,.78)' : '#fff'
}));

// TweakColor — curated color/palette picker. Each option is either a single
// hex string or an array of 1-5 hex strings; the card adapts — a lone color
// renders solid, a palette renders colors[0] as the hero (left ~2/3) with the
// rest stacked in a sharp column on the right. onChange emits the
// option in the shape it was passed (string stays string, array stays array).
// Without options it falls back to the native color input for back-compat.
function TweakColor({
  label,
  value,
  options,
  onChange
}) {
  if (!options || !options.length) {
    return /*#__PURE__*/React.createElement("div", {
      className: "twk-row twk-row-h"
    }, /*#__PURE__*/React.createElement("div", {
      className: "twk-lbl"
    }, /*#__PURE__*/React.createElement("span", null, label)), /*#__PURE__*/React.createElement("input", {
      type: "color",
      className: "twk-swatch",
      value: value,
      onChange: e => onChange(e.target.value)
    }));
  }
  // Native <input type=color> emits lowercase hex per the HTML spec, so
  // compare case-insensitively. String() guards JSON.stringify(undefined),
  // which returns the primitive undefined (no .toLowerCase).
  const key = o => String(JSON.stringify(o)).toLowerCase();
  const cur = key(value);
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-chips",
    role: "radiogroup"
  }, options.map((o, i) => {
    const colors = Array.isArray(o) ? o : [o];
    const [hero, ...rest] = colors;
    const sup = rest.slice(0, 4);
    const on = key(o) === cur;
    return /*#__PURE__*/React.createElement("button", {
      key: i,
      type: "button",
      className: "twk-chip",
      role: "radio",
      "aria-checked": on,
      "data-on": on ? '1' : '0',
      "aria-label": colors.join(', '),
      title: colors.join(' · '),
      style: {
        background: hero
      },
      onClick: () => onChange(o)
    }, sup.length > 0 && /*#__PURE__*/React.createElement("span", null, sup.map((c, j) => /*#__PURE__*/React.createElement("i", {
      key: j,
      style: {
        background: c
      }
    }))), on && /*#__PURE__*/React.createElement(__TwkCheck, {
      light: __twkIsLight(hero)
    }));
  })));
}
function TweakButton({
  label,
  onClick,
  secondary = false
}) {
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: secondary ? 'twk-btn secondary' : 'twk-btn',
    onClick: onClick
  }, label);
}
Object.assign(window, {
  useTweaks,
  TweaksPanel,
  TweakSection,
  TweakRow,
  TweakSlider,
  TweakToggle,
  TweakRadio,
  TweakSelect,
  TweakText,
  TweakNumber,
  TweakColor,
  TweakButton
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/backchain-website/tweaks-panel.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.SectionLabel = __ds_scope.SectionLabel;

__ds_ns.StatGrid = __ds_scope.StatGrid;

__ds_ns.StyledList = __ds_scope.StyledList;

__ds_ns.TextField = __ds_scope.TextField;

__ds_ns.SiteFooter = __ds_scope.SiteFooter;

__ds_ns.SiteHeader = __ds_scope.SiteHeader;

})();
