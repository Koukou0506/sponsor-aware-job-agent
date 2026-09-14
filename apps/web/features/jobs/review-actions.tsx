"use client";
import Link from "next/link"; import { Button } from "@/components/ui/button"; import { useReviewStatus } from "./api";
export function ReviewActions({jobId}:{jobId:string}){const m=useReviewStatus(jobId);return <div style={{display:"flex",gap:8,flexWrap:"wrap"}}><Link className="button primary" href={`/applications/new/${jobId}`}>Prepare Application</Link><Button onClick={()=>m.mutate("saved")}>Save</Button><Button onClick={()=>m.mutate("needs_verification")}>Needs Verification</Button><Button className="danger" onClick={()=>m.mutate("rejected")}>Reject</Button></div>}
