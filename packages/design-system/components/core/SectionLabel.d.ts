import * as React from 'react';

export interface SectionLabelProps extends React.HTMLAttributes<HTMLElement> {
  /** Element/tag to render. @default 'p' */
  as?: keyof React.JSX.IntrinsicElements;
  children?: React.ReactNode;
}

/**
 * Eyebrow / kicker — small uppercase blue label above a heading or panel.
 * 12px, Medium, wide tracking. Signals section identity.
 *
 * @startingPoint section="Core" subtitle="Uppercase blue eyebrow label" viewport="700x120"
 */
export declare function SectionLabel(props: SectionLabelProps): React.JSX.Element;
