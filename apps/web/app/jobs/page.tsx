import { Suspense } from "react"; import { JobFilters } from "@/features/jobs/job-filters"; import { JobTable } from "@/features/jobs/job-table";
export default function JobsPage(){return <div><h1>Discover Jobs</h1><p className="muted">Work authorisation is evaluated before generic match quality.</p><Suspense fallback={<p>Loading filters…</p>}><JobFilters/><JobTable/></Suspense></div>}
