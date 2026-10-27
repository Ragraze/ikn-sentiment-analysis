import type { ReactNode } from 'react';

export function PanelHeader({ title, description, children }: {
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <div className="panel-header">
      <div><h2>{title}</h2>{description && <p>{description}</p>}</div>
      {children && <div className="panel-action">{children}</div>}
    </div>
  );
}
