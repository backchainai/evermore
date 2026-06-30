import * as React from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'tertiary' | 'destructive';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.HTMLAttributes<HTMLElement> {
  /** Visual emphasis. One primary per view. @default 'primary' */
  variant?: ButtonVariant;
  /** Control height/padding. @default 'md' */
  size?: ButtonSize;
  /** When set, renders an <a> instead of <button>. */
  href?: string;
  /** Dim + block interaction; sets aria-disabled. @default false */
  disabled?: boolean;
  /** Swap label for loadingLabel and disable. @default false */
  loading?: boolean;
  /** Label shown while loading. @default 'Sending…' */
  loadingLabel?: string;
  /** Optional trailing glyph (e.g. an arrow) rendered after the label. */
  iconRight?: React.ReactNode;
  children?: React.ReactNode;
}

/**
 * Primary interactive control. Filled blue primary, hairline-bordered
 * secondary, link-style tertiary, and destructive red. Renders <a> when
 * `href` is passed (navigation) or <button> otherwise (actions).
 *
 * @startingPoint section="Core" subtitle="Buttons — primary, secondary, tertiary, destructive" viewport="700x220"
 */
export declare function Button(props: ButtonProps): React.JSX.Element;
