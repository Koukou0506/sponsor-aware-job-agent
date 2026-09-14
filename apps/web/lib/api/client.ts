const BASE=(process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/,"");
export class ApiError extends Error { constructor(public status:number, public code:string, message:string, public details:unknown={}){ super(message); } }
export async function apiFetch<T>(path:string, init?:RequestInit):Promise<T>{
  const response=await fetch(`${BASE}/api/v1${path}`,{...init,headers:{"Content-Type":"application/json",...(init?.headers??{})}});
  const body=await response.json().catch(()=>({}));
  if(!response.ok){ const err=body?.error ?? {}; throw new ApiError(response.status,err.code??"HTTP_ERROR",err.message??`HTTP ${response.status}`,err.details??{}); }
  return body as T;
}
