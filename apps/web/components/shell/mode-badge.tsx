"use client";
import { Badge } from "@/components/ui/badge"; import { useMeta } from "@/lib/api/queries";
export function ModeBadge(){ const q=useMeta(); if(q.isError) return <Badge className="bad">API offline</Badge>; if(!q.data) return <Badge>Connecting…</Badge>; return <Badge className={q.data.mode==="demo"?"warn":"good"}>{q.data.mode==="demo"?"Demo Mode":"Local Mode"}</Badge>; }
