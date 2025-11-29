import type { Metadata } from 'next';
import '../lib/theme.css';

export const metadata: Metadata = {
  title: 'Project Forge',
  description: 'Self-testing mechanical trading lab',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}


