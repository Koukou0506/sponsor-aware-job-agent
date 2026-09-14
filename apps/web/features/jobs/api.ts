import { useMutation,useQuery,useQueryClient } from "@tanstack/react-query"; import { apiFetch } from "@/lib/api/client"; import type { JobDetail,JobsPage } from "@/lib/api/types";
export type JobFilters={country?:string;role_track?:string;work_authorisation?:string;min_score?:string;company?:string;language?:string;ats?:string;page?:string;page_size?:string};
function qs(filters:JobFilters){const p=new URLSearchParams(); Object.entries(filters).forEach(([k,v])=>{if(v)p.set(k,v)}); return p.toString();}
export function useJobs(filters:JobFilters){return useQuery({queryKey:["jobs",filters],queryFn:()=>apiFetch<JobsPage>(`/jobs?${qs(filters)}`)});}
export function useJob(jobId:string){return useQuery({queryKey:["job",jobId],queryFn:()=>apiFetch<JobDetail>(`/jobs/${jobId}`),enabled:Boolean(jobId)});}
export function useReviewStatus(jobId:string){const qc=useQueryClient(); return useMutation({mutationFn:(status:string)=>apiFetch<JobDetail>(`/jobs/${jobId}/review-status`,{method:"POST",body:JSON.stringify({status})}),onSuccess:()=>{qc.invalidateQueries({queryKey:["job",jobId]});qc.invalidateQueries({queryKey:["jobs"]});}})}
