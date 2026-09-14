import { useMutation,useQuery,useQueryClient } from "@tanstack/react-query"; import { apiFetch } from "@/lib/api/client";
export type RouteRow={job_id?:string;country:string;status:string;route?:string;confidence?:number|null;ruleset_version?:string|null;evidence?:Array<Record<string,unknown>|string>;unresolved?:string[]};
export function useRoutes(){return useQuery({queryKey:["immigration-routes"],queryFn:()=>apiFetch<RouteRow[]>("/immigration/routes")});}
export function useRegistries(){return useQuery({queryKey:["registry-status"],queryFn:()=>apiFetch<Array<Record<string,unknown>>>("/immigration/registries/status")});}
export function useReassess(){const qc=useQueryClient();return useMutation({mutationFn:(jobId:string)=>apiFetch(`/immigration/reassess/${jobId}`,{method:"POST",body:"{}"}),onSuccess:()=>qc.invalidateQueries({queryKey:["immigration-routes"]})});}
