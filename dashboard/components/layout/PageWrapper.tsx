import type { ReactNode } from "react";

interface PageWrapperProps {
  children: ReactNode;
  className?: string;
}

// Centered, max-width page container shared by every dashboard route.
export function PageWrapper({
  children,
  className = "",
}: PageWrapperProps) {
  return (
    <main className={`max-w-6xl mx-auto px-5 py-10 ${className}`}>
      {children}
    </main>
  );
}
