import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'mlspend | Cost ownership', description: 'ML cost allocation, simulated showback and documented shadow prices. Built for Ajay Mekala.' };
export default function Layout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="en" suppressHydrationWarning><body>{children}</body></html>;
}
