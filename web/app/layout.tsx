import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Konsilisyum - Yaşayan Fikir Meclisi',
  description: 'Terminal tabanlı yaşayan fikir meclisi',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="tr">
      <body className="min-h-screen">{children}</body>
    </html>
  )
}
