import { Badge } from "@/components/ui/badge";
export function WorkAuthorisationBadge({status}:{status:string}){const c=status==="eligible"?"good":status==="likely"?"good":status==="ineligible"?"bad":"warn"; return <Badge className={c}>{status}</Badge>}
