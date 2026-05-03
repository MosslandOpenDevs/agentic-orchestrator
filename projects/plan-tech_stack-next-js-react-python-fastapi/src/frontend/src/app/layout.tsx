import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'plan-tech_stack-next-js-react-python-fastapi',
  description: 'I believe this initial plan provides a solid foundation.  Let's schedule a follow-up meeting to disc',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
          {children}
        </div>
      </body>
    </html>
  );
}
