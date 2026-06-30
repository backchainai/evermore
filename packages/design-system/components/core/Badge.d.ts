import * as React from 'react';

export type BadgeVariant = 'neutral' | 'info' | 'accent' | 'success' | 'error';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Color treatment. @default 'neutral' */
  variant?: BadgeVariant;
  children?: React.ReactNode;
}

/**
 * Small inline pill for status, category, or metadata. Tinted background
 * with matching text — never color alone for meaning.
 *
 * @startingPoint section="Core" subtitle="Status & category pills" viewport="700x150"
 */
export declare function Badge(props: BadgeProps): React.JSX.Element;
