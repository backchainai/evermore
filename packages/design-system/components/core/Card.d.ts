import * as React from 'react';

export type CardPadding = 'sm' | 'md' | 'lg';

export interface CardProps extends React.HTMLAttributes<HTMLElement> {
  /** Inner padding. @default 'md' */
  padding?: CardPadding;
  /** Adds hover lift + pointer; makes the card focusable. @default false */
  interactive?: boolean;
  /** Element/tag to render. @default 'div' */
  as?: keyof React.JSX.IntrinsicElements;
  children?: React.ReactNode;
}

/**
 * The primary layout primitive. Flat white surface with a hairline alpha
 * border and no drop shadow (shadows are reserved for floating UI). Wrap in
 * an `.on-slate` ancestor and it composites as alpha-white on dark.
 *
 * @startingPoint section="Core" subtitle="Flat surface card with hairline border" viewport="700x200"
 */
export declare function Card(props: CardProps): React.JSX.Element;
