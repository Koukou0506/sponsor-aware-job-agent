import { useQuery } from "@tanstack/react-query"; import { apiFetch } from "@/lib/api/client";
export type SettingsSummary={mode:string;database:Record<string,unknown>;candidate_profile:Record<string,unknown>;registries:Record<string,unknown>;browser_profile:Record<string,unknown>;llm:Record<string,unknown>};
export function useSettingsSummary(){return useQuery({queryKey:["settings-summary"],queryFn:()=>apiFetch<SettingsSummary>("/settings/summary")});}
