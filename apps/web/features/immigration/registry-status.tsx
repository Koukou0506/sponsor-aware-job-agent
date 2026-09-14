import { Card } from "@/components/ui/card";
export function RegistryStatus({items}:{items:Array<Record<string,unknown>>}){return <Card><h3>Registry status</h3>{items.length?<ul>{items.map((x,i)=><li key={i}>{String(x.country??"registry")}: {String(x.status??x.freshness??"available")}</li>)}</ul>:<p className="muted">No registry freshness metadata exposed.</p>}</Card>}
