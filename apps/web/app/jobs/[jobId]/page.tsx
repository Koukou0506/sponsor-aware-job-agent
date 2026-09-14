"use client"; import { useParams } from "next/navigation"; import { JobDetailView } from "@/features/jobs/job-detail";
export default function Page(){const p=useParams<{jobId:string}>();return <JobDetailView jobId={p.jobId}/>}
