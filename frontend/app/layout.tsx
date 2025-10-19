import "./globals.css";

import { TrpcProvider } from "../lib/trpc/provider";

export const metadata = {
  title: "Creative Workforce PoC",
  description: "Creative Workforce PoC Console",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className="bg-slate-950 text-slate-100">
        <TrpcProvider>{children}</TrpcProvider>
      </body>
    </html>
  );
}
