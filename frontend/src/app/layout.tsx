import './globals.css';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

export const metadata = {
  title: 'ResearchMatch - Scholarly Paper Discovery & Literature Review',
  description: 'Discover relevant research papers, browse by subject, and match your proposed research objectives with connected scholarly sources.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="bg-gray-950 text-white min-height-screen flex flex-col antialiased" suppressHydrationWarning>
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
