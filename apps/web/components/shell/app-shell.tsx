"use client";
import Link from "next/link"; import { ModeBadge } from "./mode-badge";
const links=[["/","Dashboard"],["/jobs","Discover Jobs"],["/applications","Applications"],["/resume","Resume & Facts"],["/immigration","Immigration"],["/settings","Settings"]];
export function AppShell({children}:{children:React.ReactNode}){return <div className="shell"><aside className="sidebar"><div className="brand">Sponsor-Aware Job Agent</div><div className="muted">Evidence-first applications</div><nav className="nav">{links.map(([href,label])=><Link key={href} href={href}>{label}</Link>)}</nav></aside><main className="main"><header className="topbar"><strong>Job Search Workspace</strong><ModeBadge/></header><div className="content">{children}</div></main></div>}
