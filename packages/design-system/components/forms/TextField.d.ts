import * as React from 'react';

export interface TextFieldProps extends React.InputHTMLAttributes<HTMLInputElement & HTMLTextAreaElement> {
  /** Field label rendered above the control. */
  label?: string;
  /** Explicit id; auto-generated when omitted. */
  id?: string;
  /** Adds a required marker and aria-required. @default false */
  required?: boolean;
  /** Error message — sets error state, icon + red text. */
  error?: string | null;
  /** Success message — sets success state, icon + green text. */
  success?: string | null;
  /** Helper text shown when no error/success. */
  hint?: string | null;
  /** Render a <textarea> instead of <input>. @default false */
  multiline?: boolean;
}

/**
 * Labelled text input (or textarea via `multiline`) with the full state
 * system: default / focus / error / success / disabled. Errors and successes
 * pair an icon with text, never color alone.
 *
 * @startingPoint section="Forms" subtitle="Text input & textarea with validation states" viewport="700x260"
 */
export declare function TextField(props: TextFieldProps): React.JSX.Element;
