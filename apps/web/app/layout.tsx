import "./globals.css"; import { QueryProvider } from "@/components/providers/query-provider"; import { AppShell } from "@/components/shell/app-shell";
export const metadata={title:"Sponsor-Aware Job Agent",description:"Sponsor-aware job discovery and supervised application workspace"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><QueryProvider><AppShell>{children}</AppShell></QueryProvider></body></html>}
