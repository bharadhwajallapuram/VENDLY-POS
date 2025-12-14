import type { Metadata } from 'next';
import '@/styles/globals.css';
import Nav from '@/components/Nav';

export const metadata: Metadata = {
  title: 'Vendly POS',
  description: 'Professional Point of Sale System',
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 5,
    userScalable: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Vendly POS" />
      </head>
      <body className="min-h-screen bg-gray-50">
        <Nav />
        <main className="max-w-7xl mx-auto py-4 md:py-6 px-3 md:px-4">
          {children}
        </main>
      </body>
    </html>
  );
}
