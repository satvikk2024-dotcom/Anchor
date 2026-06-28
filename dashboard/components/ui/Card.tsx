import type { ReactNode, HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export default function Card({ children, className = "", ...rest }: CardProps) {
  return (
    <div
      className={`rounded-card border border-border-default bg-bg-surface ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}
