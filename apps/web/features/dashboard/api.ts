import { useQuery } from "@tanstack/react-query"; import { apiFetch } from "@/lib/api/client"; import type { Dashboard } from "@/lib/api/types";
export function useDashboard(){ return useQuery({queryKey:["dashboard"],queryFn:()=>apiFetch<Dashboard>("/dashboard")}); }
